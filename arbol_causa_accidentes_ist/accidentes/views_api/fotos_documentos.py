# accidentes/views_api/fotos_documentos.py
# -*- coding: utf-8 -*-

import os
import uuid
from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseNotAllowed, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.template.loader import render_to_string
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.middleware.csrf import get_token

from accidentes.utils.mixins import AnchorRedirectMixin, AccidenteScopedByCodigoMixin
from accidentes.forms import DocumentForm
from accidentes.models import Accidentes, Documentos


class FotosDocumentosView(LoginRequiredMixin, AccidenteScopedByCodigoMixin, AnchorRedirectMixin, View):
    """
    Seguridad / alcance:
      - El accidente se resuelve con self.accidente_from(codigo), que usa get_accidente_scoped_or_404
        (404 si no existe o está fuera de alcance) y sincroniza session['accidente_id'].
      - TODAS las operaciones de lectura/escritura filtran por accidente=...
      - No se revela existencia de recursos fuera de alcance (404 coherente en toda la app).
    """
    template_name = "accidentes/fotos_documentos.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = FileSystemStorage(
            location=Path(settings.PROTECTED_MEDIA_ROOT) / "documentos"
        )

    # ---- util: redirección con anchor y soporte HTMX (usar el mixin) ----
    def _redirect_anchor(self, request, url_name, codigo, anchor=None):
        url = reverse(url_name, args=[codigo]) if codigo else reverse(url_name)
        if anchor:
            url = f"{url}#{anchor}"
        if request.headers.get("HX-Request"):
            # En HTMX devolvemos 204 para que la página no navegue; los mensajes se muestran igual.
            return HttpResponse(status=204)
        return HttpResponseRedirect(url)

    # ---- util: serializar modelo a item dict para el partial ----
    def _doc_to_item(self, doc: Documentos):
        is_http = bool(doc.url and str(doc.url).lower().startswith(("http://", "https://")))
        has_file = bool(doc.nombre_archivo)
        return {
            "pk": doc.documento_id,
            "title": doc.documento or (doc.nombre_archivo or "(enlace)"),
            "objetivo": getattr(doc, "objetivo", "") or "",
            "url": doc.url if is_http else None,            # Enlace externo (clic directo)
            "download_id": doc.documento_id if has_file and not is_http else None,  # Descarga protegida vía view
            "has_content": bool(doc.url or doc.nombre_archivo),
        }

    # ---- util: renderizar la .col completa con la tarjeta ----
    def _render_col(self, request, codigo, item):
        card_html = render_to_string(
            "accidentes/partials/docs/_doc_card.html",
            {"item": item, "codigo": codigo},
            request=request,  # context processors (csrf, messages, etc.)
        )
        return f'<div class="col" id="doc-{item["pk"]}">{card_html}</div>'

    # ========================= GET =========================
    def get(self, request, codigo: str):
        # 404 si el accidente no existe o está fuera de alcance; también sincroniza la sesión.
        accidente: Accidentes = self.accidente_from(codigo)

        # Sugeridos "vacíos" (creados por IA sin contenido aún)
        suggested = Documentos.objects.filter(
            accidente=accidente,
            url__isnull=True,
            nombre_archivo__isnull=True
        )

        # Todo lo que haya para el accidente (con o sin contenido)
        uploaded = Documentos.objects.filter(accidente=accidente)

        uploaded_map = {f.documento_id: self._doc_to_item(f) for f in uploaded}

        items = []
        for s in suggested:
            item = uploaded_map.get(s.documento_id)
            if item and item["has_content"]:
                items.append(item)
            else:
                items.append({
                    "pk": s.documento_id,
                    "title": s.documento,
                    "objetivo": getattr(s, "objetivo", "") or "",
                    "url": None,
                    "download_id": None,
                    "has_content": False,
                })

        suggested_ids = set(s.documento_id for s in suggested)
        for f_id, it in uploaded_map.items():
            if f_id not in suggested_ids:
                items.append(it)

        # Orden: primero los pendientes, luego con contenido; después por título
        items.sort(key=lambda x: (x["has_content"], (x["title"] or "").lower()))

        form = DocumentForm()
        return render(request, self.template_name, {
            "items": items,
            "form": form,
            "codigo": codigo,
        })

    # ========================= POST =========================
    def post(self, request, codigo: str):
        accidente: Accidentes = self.accidente_from(codigo)
        action = (request.POST.get("action") or "").strip()

        # ---- Completar pendiente (HTMX reemplaza la tarjeta) ---
        if action == "complete_pending":
            doc_id = request.POST.get("doc_id")
            link   = (request.POST.get("link") or "").strip()
            file   = request.FILES.get("file")
            anchor = request.POST.get("anchor")

            # Exclusión: exactamente uno
            if bool(link) == bool(file):
                messages.error(request, "Debes ingresar solo uno: URL o archivo.")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            # Validar URL externa
            if link and not link.lower().startswith(("http://", "https://")):
                messages.error(request, "La URL debe comenzar con http:// o https://")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            doc = Documentos.objects.filter(accidente=accidente, documento_id=doc_id).first()
            if not doc:
                messages.error(request, "Documento no encontrado.")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            if link:
                # limpiar archivo previo (si hubiera) y setear URL
                if doc.nombre_archivo:
                    ext = os.path.splitext(doc.nombre_archivo)[1]
                    path = f"{doc.documento_id}{ext}"
                    if self.storage.exists(path):
                        self.storage.delete(path)
                doc.url = link
                doc.nombre_archivo = None
                doc.mime_type = None
            else:
                # limpiar URL previa (si hubiera) y guardar archivo
                doc.url = None
                ext = os.path.splitext(file.name)[1]
                filename = f"{doc.documento_id}{ext}"
                self.storage.save(filename, file)
                doc.nombre_archivo = file.name
                doc.mime_type = file.content_type or ""
                doc.url = f"{settings.PROTECTED_MEDIA_URL}documentos/{filename}"
            doc.save()

            if request.headers.get("HX-Request"):
                item = self._doc_to_item(doc)
                html = self._render_col(request, codigo, item)
                return HttpResponse(html)

            messages.success(request, "Documento actualizado.")
            return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

        # ---- Añadir documento (modal HTMX: insert al final) ----
        if action == "add_free_docs":
            title = (request.POST.get("doc_title") or "").strip()
            obj   = (request.POST.get("doc_objective") or "").strip()
            url   = (request.POST.get("doc_url") or "").strip()
            f     = request.FILES.get("doc_file")
            anchor = request.POST.get("anchor") or "grid-documentos"

            # Exclusión: exactamente uno
            if (not url and not f) or (url and f):
                messages.error(request, "Debes ingresar URL o archivo (no ambos).")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            if url and not url.lower().startswith(("http://", "https://")):
                messages.error(request, "La URL debe comenzar con http:// o https://")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            # ¿Actualizar existente por título+objetivo? (dentro del mismo accidente)
            existing_doc = None
            if title or obj:
                existing_doc = Documentos.objects.filter(
                    accidente=accidente, documento=title, objetivo=obj
                ).first()

            if existing_doc:
                if url:
                    # limpiar archivo anterior si lo hubiera
                    if existing_doc.nombre_archivo:
                        ext = os.path.splitext(existing_doc.nombre_archivo)[1]
                        path = f"{existing_doc.documento_id}{ext}"
                        if self.storage.exists(path):
                            self.storage.delete(path)
                    existing_doc.url = url
                    existing_doc.nombre_archivo = None
                    existing_doc.mime_type = None
                else:
                    # limpiar url anterior si lo hubiera
                    existing_doc.url = None
                    ext = os.path.splitext(f.name)[1]
                    filename = f"{existing_doc.documento_id or uuid.uuid4()}{ext}"
                    self.storage.save(filename, f)
                    existing_doc.url = f"{settings.PROTECTED_MEDIA_URL}documentos/{filename}"
                    existing_doc.nombre_archivo = f.name
                    existing_doc.mime_type = f.content_type or ""
                existing_doc.save()
                doc = existing_doc
            else:
                new_id = str(uuid.uuid4())
                if url:
                    doc = Documentos.objects.create(
                        accidente=accidente,
                        documento_id=new_id,
                        documento=title or url,
                        objetivo=obj,
                        url=url
                    )
                else:
                    ext = os.path.splitext(f.name)[1]
                    filename = f"{new_id}{ext}"
                    self.storage.save(filename, f)
                    doc = Documentos.objects.create(
                        accidente=accidente,
                        documento_id=new_id,
                        documento=title or f.name,
                        objetivo=obj,
                        nombre_archivo=f.name,
                        mime_type=f.content_type or "",
                        url=f"{settings.PROTECTED_MEDIA_URL}documentos/{filename}"
                    )

            if request.headers.get("HX-Request"):
                item = self._doc_to_item(doc)
                html = self._render_col(request, codigo, item)
                
                # Contar documentos totales después de agregar
                total_docs = Documentos.objects.filter(accidente=accidente).count()
                
                # OOB para eliminar placeholder si existe
                oob_delete = '<div id="empty-docs" hx-swap-oob="delete"></div>'
                
                # Si es el primer documento, agregar botón "Guardar todo" con OOB
                save_button = ''
                if total_docs == 1:
                    csrf_token = get_token(request)
                    save_button = f'''
                        <div class="d-flex justify-content-start mt-4" id="final-action-section" hx-swap-oob="afterend:#grid-documentos">
                            <form method="post" action="{reverse('accidentes:ia_fotos', args=[codigo])}">
                                <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                                <input type="hidden" name="action" value="save_all">
                                <input type="hidden" name="anchor" value="final-action-section">
                                <button type="submit" class="btn btn-primary-custom">Guardar todo</button>
                            </form>
                        </div>
                    '''
                
                resp = HttpResponse(html + oob_delete + save_button)
                resp["HX-Trigger"] = "doc-added"
                return resp

            messages.success(request, "Documento agregado.")
            return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, "grid-documentos")

        # ---- Compat: suggested_submit ----
        if action == "suggested_submit":
            rec_id = request.POST.get("suggested_id")
            link   = (request.POST.get("link") or "").strip()
            file   = request.FILES.get("file")
            anchor = request.POST.get("anchor")

            if bool(link) == bool(file):
                messages.error(request, "Debes ingresar solo uno: enlace O archivo.")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            if link and not link.lower().startswith(("http://", "https://")):
                messages.error(request, "La URL debe comenzar con http:// o https://")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            doc = Documentos.objects.filter(accidente=accidente, documento_id=rec_id).first()
            if not doc:
                messages.error(request, "Documento sugerido no encontrado.")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            if link:
                if doc.nombre_archivo:
                    ext = os.path.splitext(doc.nombre_archivo)[1]
                    path = f"{doc.documento_id}{ext}"
                    if self.storage.exists(path):
                        self.storage.delete(path)
                doc.url = link
                doc.nombre_archivo = None
                doc.mime_type = None
            else:
                doc.url = None
                ext = os.path.splitext(file.name)[1]
                filename = f"{rec_id}{ext}"
                self.storage.save(filename, file)
                doc.nombre_archivo = file.name
                doc.mime_type = file.content_type or ""
                doc.url = f"{settings.PROTECTED_MEDIA_URL}documentos/{filename}"
            doc.save()

            if request.headers.get("HX-Request"):
                item = self._doc_to_item(doc)
                html = self._render_col(request, codigo, item)
                return HttpResponse(html)

            messages.success(request, "Documento guardado correctamente.")
            return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

        # ---- NUEVO: Limpiar contenido (archivo/enlace) pero mantener la tarjeta ----
        if action == "clear_content":
            doc_id = request.POST.get("doc_id")
            anchor = request.POST.get("anchor") or "grid-documentos"

            if not doc_id:
                messages.error(request, "No se indicó documento a limpiar.")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            doc = Documentos.objects.filter(accidente=accidente, documento_id=doc_id).first()
            if not doc:
                messages.error(request, "Documento no encontrado.")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            # Borrar archivo físico si existe
            if doc.nombre_archivo:
                ext = os.path.splitext(doc.nombre_archivo)[1]
                path = f"{doc.documento_id}{ext}"
                if self.storage.exists(path):
                    self.storage.delete(path)

            # Limpiar campos de contenido
            doc.url = None
            doc.nombre_archivo = None
            doc.mime_type = None
            doc.save()

            if request.headers.get("HX-Request"):
                item = self._doc_to_item(doc)  # ahora has_content = False
                html = self._render_col(request, codigo, item)
                return HttpResponse(html)

            messages.success(request, "Contenido eliminado. Puedes subir un nuevo archivo o URL.")
            return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

        # ---- Eliminar (borra registro + archivo y quita tarjeta) ----
        if action == "delete":
            doc_id = request.POST.get("doc_id")
            anchor = request.POST.get("anchor") or "grid-documentos"

            if not doc_id:
                messages.error(request, "No se indicó documento a eliminar.")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

            doc = Documentos.objects.filter(accidente=accidente, documento_id=doc_id).first()
            if doc:
                if doc.nombre_archivo:
                    ext = os.path.splitext(doc.nombre_archivo)[1]
                    path = f"{doc.documento_id}{ext}"
                    if self.storage.exists(path):
                        self.storage.delete(path)
                doc.delete()
                
                messages.success(request, "Documento eliminado correctamente.")
                
                if request.headers.get("HX-Request"):
                    # Verificar si quedan documentos
                    remaining_docs = Documentos.objects.filter(accidente=accidente).count()
                    
                    notification_html = render_to_string("accidentes/notification.html", {}, request=request)
                    
                    if remaining_docs == 0:
                        # Si no quedan documentos, mostrar placeholder vacío Y ocultar botón "Guardar todo"
                        # Usamos beforeend en el grid para que aparezca dentro del grid y no después
                        empty_placeholder = '''
                            <div class="col-12" id="empty-docs" hx-swap-oob="beforeend:#grid-documentos">
                                <div class="empty-state text-center py-4">
                                    <i class="fa-solid fa-inbox fa-3x text-muted mb-3"></i>
                                    <p class="text-muted">No hay documentos aún. Utiliza el botón "Añadir documento" para comenzar.</p>
                                </div>
                            </div>
                        '''
                        # Ocultar el botón "Guardar todo" reemplazándolo con un div vacío
                        hide_button = '<div id="final-action-section" hx-swap-oob="outerHTML"></div>'
                        return HttpResponse(notification_html + empty_placeholder + hide_button)
                    else:
                        # Solo notificación si quedan documentos
                        return HttpResponse(notification_html)
                
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)
            else:
                messages.error(request, "Documento no encontrado en la base de datos.")
                return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

        # ---- Guardar todo y continuar (navegación normal) ----
        if action == "save_all":
            messages.success(request, "Todos los documentos están guardados.")
            anchor = request.POST.get("anchor") or "grid-documentos"
            return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, anchor)

        # Fallback: evita None/acciones no soportadas
        messages.error(request, "Acción no reconocida.")
        return self._redirect_anchor(request, "accidentes:ia_fotos", codigo, "grid-documentos")
