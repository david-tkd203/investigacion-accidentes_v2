# adminpanel/admin_function/descargar_informe.py
from __future__ import annotations

import mimetypes
from io import BytesIO
from pathlib import Path
from urllib.parse import quote as url_quote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404

from accidentes.models import Accidentes, Informes, Documentos

ALLOWED_ROLES = {"admin", "admin_ist", "admin_holding", "admin_empresa"}


def _user_can_download(user, accidente: Accidentes | None) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "rol", None) in ALLOWED_ROLES:
        return True
    if accidente is None:
        return False
    return accidente.usuario_asignado_id == getattr(user, "id", None)


def _guess_mime(path_or_name: str, fallback: str = "application/octet-stream") -> str:
    mimetypes.add_type(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
        strict=False,
    )
    return mimetypes.guess_type(path_or_name)[0] or fallback


def _safe_disp(name: str) -> str:
    base = (name or "archivo").strip() or "archivo"
    ascii_name = "".join(ch if 32 <= ord(ch) < 127 else "_" for ch in base)
    utf8_name = url_quote(base)
    return f'filename="{ascii_name}"; filename*=UTF-8\'\'{utf8_name}'


def _x_accel_response(abs_path: Path, download_name: str) -> HttpResponse:
    """
    Sirve con Nginx interno según tu config:
      location /protected_media_internal/ {
          internal;
          alias /usr/src/app/protected_media/;
      }
    """
    root = Path(settings.PROTECTED_MEDIA_ROOT)
    try:
        rel = abs_path.relative_to(root).as_posix()
    except Exception:
        raise Http404("Ruta inválida.")

    if not abs_path.exists() or not abs_path.is_file():
        raise Http404("Archivo no encontrado.")

    internal_url = f"/protected_media_internal/{rel}"
    resp = HttpResponse()
    resp["Content-Type"] = _guess_mime(abs_path.name)
    resp["Content-Disposition"] = f"attachment; {_safe_disp(download_name)}"
    resp["X-Accel-Redirect"] = internal_url
    resp["X-Content-Type-Options"] = "nosniff"
    resp["Cache-Control"] = "private, max-age=0, no-cache"
    return resp


def _serve_document_from_db_or_fs(doc: Documentos) -> HttpResponse:
    # Enlace externo → no descargamos
    if doc.url and str(doc.url).lower().startswith(("http://", "https://")):
        raise Http404("Este documento es un enlace externo.")

    # Binario en BD
    if doc.contenido:
        bin_data = doc.contenido
        try:
            if isinstance(bin_data, memoryview):
                bin_data = bin_data.tobytes()
            elif isinstance(bin_data, bytearray):
                bin_data = bytes(bin_data)
            elif not isinstance(bin_data, (bytes, bytearray)):
                bin_data = bytes(bin_data)
        except Exception:
            raise Http404("No se pudo leer el archivo.")

        filename = (doc.nombre_archivo or f"documento_{doc.documento_id}").strip() or f"documento_{doc.documento_id}"
        ctype = doc.mime_type or _guess_mime(filename)
        return FileResponse(BytesIO(bin_data), as_attachment=True, filename=filename, content_type=ctype)

    # Fichero físico: protected_media/documentos/<id><ext>
    if not doc.nombre_archivo:
        raise Http404("El documento no tiene archivo asociado.")

    ext = Path(doc.nombre_archivo).suffix or ".bin"
    phys = Path(settings.PROTECTED_MEDIA_ROOT) / "documentos" / f"{doc.documento_id}{ext}"
    if not phys.exists():
        raise Http404("Archivo no encontrado.")

    return _x_accel_response(phys, doc.nombre_archivo)


def _find_informe_file(acc: Accidentes, inf: Informes) -> Path | None:
    """
    Busca DOCX en:
      protected_media/informes/<CODIGO_ACCIDENTE>/*.docx
    Prioriza archivos cuyo nombre contenga el código del informe; si no, el más reciente.
    """
    root = Path(settings.PROTECTED_MEDIA_ROOT)
    base = root / "informes"
    if not base.exists():
        return None

    case_dir = base / (acc.codigo_accidente or "").strip()
    candidates = []
    if case_dir.is_dir():
        candidates = list(case_dir.glob("*.docx"))

    if not candidates:
        candidates = list(base.glob("*.docx"))

    if not candidates:
        return None

    inf_code = ((getattr(inf, "codigo", "") or "")).lower()

    def pick_best(files):
        if inf_code:
            with_code = [p for p in files if inf_code in p.name.lower()]
            if with_code:
                with_code.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                return with_code[0]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0]

    return pick_best(candidates)


@login_required
def descargar_informe(request, codigo: str):
    """
    Descarga el informe vigente (.docx) del accidente `codigo` desde:
      protected_media/informes/<codigo>/*.docx
    Fallback: intenta un Documento asociado al caso si no hay DOCX en disco.
    """
    acc = get_object_or_404(Accidentes, codigo_accidente=codigo)
    if not _user_can_download(request.user, acc):
        raise Http404("No autorizado o caso no disponible.")

    inf = (
        Informes.objects
        .filter(accidente_id=acc.pk, is_current=True)
        .order_by("-version", "-created_at")
        .first()
    )
    if not inf:
        raise Http404("Este caso no tiene un informe vigente.")

    fpath = _find_informe_file(acc, inf)
    if fpath:
        return _x_accel_response(fpath, fpath.name)

    # Fallback: intenta localizar un Documentos “informe”
    docs = Documentos.objects.filter(accidente_id=acc.pk)

    doc = None
    code = (getattr(inf, "codigo", "") or "").strip()
    if code:
        doc = (
            docs.filter(
                Q(nombre_archivo__icontains=code) |
                Q(documento__icontains=code) |
                Q(objetivo__icontains=code)
            )
            .order_by("-subido_el")
            .first()
        )

    if not doc:
        KEYWORDS = ["informe", "reporte", "report"]
        qk = Q()
        for k in KEYWORDS:
            qk |= Q(objetivo__icontains=k) | Q(nombre_archivo__icontains=k) | Q(documento__icontains=k)
        doc = (
            docs.filter(
                qk |
                Q(nombre_archivo__iendswith=".docx") |
                Q(mime_type__icontains="officedocument") |
                Q(nombre_archivo__iendswith=".pdf") |
                Q(mime_type__icontains="pdf")
            )
            .order_by("-subido_el")
            .first()
        )

    if doc:
        return _serve_document_from_db_or_fs(doc)

    raise Http404("Archivo de informe no disponible por el momento.")


# ===== también expone descargar_documento (lo requiere tu urls.py) =====
@login_required
def descargar_documento(request, doc_id: int):
    """
    Descarga segura de un documento por ID, replicando el patrón que ya usabas.
    """
    doc = get_object_or_404(Documentos, pk=doc_id)
    acc = getattr(doc, "accidente", None)
    if not acc:
        raise Http404("Documento no asociado a un caso.")
    if not _user_can_download(request.user, acc):
        raise Http404("No autorizado o documento no disponible.")

    # Enlace externo → no descargamos
    if doc.url and str(doc.url).lower().startswith(("http://", "https://")):
        raise Http404("Este documento es un enlace externo.")

    # Binario en BD
    if doc.contenido:
        bin_data = doc.contenido
        try:
            if isinstance(bin_data, memoryview):
                bin_data = bin_data.tobytes()
            elif isinstance(bin_data, bytearray):
                bin_data = bytes(bin_data)
            elif not isinstance(bin_data, (bytes, bytearray)):
                bin_data = bytes(bin_data)
        except Exception:
            raise Http404("No se pudo leer el archivo.")

        filename = (doc.nombre_archivo or f"documento_{doc.documento_id}").strip() or f"documento_{doc.documento_id}"
        ctype = doc.mime_type or _guess_mime(filename)
        return FileResponse(BytesIO(bin_data), as_attachment=True, filename=filename, content_type=ctype)

    # Fichero físico: protected_media/documentos/<id><ext>
    if not doc.nombre_archivo:
        raise Http404("El documento no tiene archivo asociado.")

    ext = Path(doc.nombre_archivo).suffix or ".bin"
    phys = Path(settings.PROTECTED_MEDIA_ROOT) / "documentos" / f"{doc.documento_id}{ext}"
    if not phys.exists():
        raise Http404("Archivo no encontrado.")

    return _x_accel_response(phys, doc.nombre_archivo)
