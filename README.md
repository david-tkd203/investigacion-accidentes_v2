# IST Investiga — Asistente de Accidentes (Django)

Plataforma web para **investigar accidentes laborales** con apoyo de **IA**, formularios guiados, gestión de documentos y **trazabilidad** de punta a punta. Orquesta entrevistas, relato, hechos, árbol de causa, medidas correctivas e informe final en un flujo único.

> Este README integra: la documentación existente del proyecto, la estructura real del repositorio y una guía extendida para desarrollo, despliegue y operación.

---

## Índice
- [Contexto y Problema](#contexto-y-problema)
- [Objetivo General y Específicos](#objetivo-general-y-específicos)
- [Arquitectura y Tecnologías](#arquitectura-y-tecnologías)
- [Estructura de Directorios (raíz)](#estructura-de-directorios-raíz)
- [Módulos y Detalle de Carpetas](#módulos-y-detalle-de-carpetas)
  - [core/](#core)
  - [accidentes/](#accidentes)
  - [adminpanel/](#adminpanel)
  - [accounts/](#accounts)
- [Roles del Sistema](#roles-del-sistema)
- [Flujo de Uso (Guía de Usuario)](#flujo-de-uso-guía-de-usuario)
- [Seguridad y Cumplimiento](#seguridad-y-cumplimiento)
- [Configuración, Desarrollo y Scripts](#configuración-desarrollo-y-scripts)
- [Despliegue (Docker Compose)](#despliegue-docker-compose)
- [Pruebas](#pruebas)
- [Roadmap](#roadmap)
- [Créditos](#créditos)

---

## Contexto y Problema

- La investigación de accidentes suele tener **fuentes de información dispersas** (correos, planillas, repositorios ad hoc), generando pérdidas de evidencia, duplicidades y versiones incongruentes.
- Falta de **estandarización en cuestionarios** y guías, lo que provoca omisiones de preguntas clave, vacíos en la cronología y baja trazabilidad.
- Uso de **IA** como componente aislado, sin integración con formularios, evidencia y controles de versión.
- Riesgos legales y de cumplimiento por auditoría limitada y trazabilidad débil.

La plataforma apunta a unificar datos, estandarizar cuestionarios, **orquestar la IA dentro del proceso** y garantizar la **trazabilidad de extremo a extremo**.

---

## Objetivo General y Específicos

**Objetivo General**  
Diseñar e implementar una plataforma web integrada, basada en **Django** e **IA**, que automatice y centralice el flujo completo de investigación de accidentes laborales (entrevistas → evidencias → relato → hechos → árbol de causas → medidas → informe final).

**Objetivos Específicos**
1. **Estandarizar** la generación de cuestionarios con IA, cubriendo factores técnicos, organizacionales y humanos.
2. **Integrar** gestión documental (subida y vinculación de archivos y enlaces) con el flujo del caso.
3. **Centralizar** respuestas y evidencias (BD relacional + repositorio JSON) y habilitar informes con 1 clic.
4. **Controlar calidad** con validaciones y alertas de campos faltantes para evitar rechazos administrativos.
5. **Roles y permisos** con auditoría (quién hizo qué y cuándo).

---

## Arquitectura y Tecnologías

- **Backend:** Django + Python (apps: `accidentes`, `adminpanel`, `accounts`, `core`).
- **Base de datos:** MySQL.
- **Frontend:** Plantillas HTML + CSS/JS ligeros.
- **IA Service:** utilidades y prompts versionados (`accidentes/setting/prompt/prompt.json`, `views_ia.py`, `views_api/prompt_utils.py`).
- **Almacenamiento:** 
  - Ficheros en `protected_media/` (p. ej., `documentos/`, `informes/`).
  - Estáticos en `static/` y `accidentes/static/accidentes/` (CSS/IMG).
- **Despliegue:** Docker Compose (servicios `web`, `db`, `nginx`).

---

## Estructura de Directorios (raíz)

```text
arbol_causa_accidentes_ist/
├─ core/               — Configuración Django (settings, urls, asgi, wsgi), email/services/utils.
├─ accidentes/         — App principal: modelos, vistas, formularios, servicios; templates y estáticos propios.
├─ adminpanel/         — Panel por investigación: vistas/urls/forms, plantillas del panel y estilos.
├─ accounts/           — Autenticación/usuarios: backends, forms, migraciones y templates de login/reset.
├─ templates/          — Plantillas globales.
├─ static/             — Estáticos globales (css, img, js).
├─ utils/              — Utilidades transversales.
├─ config/             — Config/datos auxiliares (p. ej., accidentes_demo.json).
├─ nginx/              — Configuración Nginx (investiga-app.conf).
├─ protected_media/    — Archivos subidos/generados (documentos, informes). No se versiona.
└─ mysql/              — Datos locales de MySQL (binlogs/metadata). No se versiona.
```

> **Tip:** Puedes copiar este bloque tal cual en el `README.md` o generar una versión PNG para presentaciones.

---

## Módulos y Detalle de Carpetas

### core/

```text
core/                              — Configuración base de Django y utilidades del proyecto
├─ asgi.py                         — Entrada ASGI
├─ settings.py                     — Config del proyecto (apps, DB, static, email, etc.)
├─ urls.py                         — Enrutamiento raíz
├─ wsgi.py                         — Entrada WSGI
├─ __init__.py
├─ email_backends/
│  ├─ ist_via_token.py            — Backend de email con token
│  └─ __init__.py
├─ services/
│  ├─ apiemail.py                  — Cliente/servicio de email
│  └─ __init__.py
└─ utils/
   ├─ token.py                     — Helpers de tokens/firmas
   └─ __init__.py
```

---

### accidentes/

**Árbol de la app y archivos principales**

```text
accidentes/
├─ access.py
├─ admin.py
├─ apps.py
├─ carga_datos_json.py
├─ context_processor.py
├─ context_processors.py
├─ decorators.py
├─ forms.py
├─ managers.py
├─ models.py
├─ permissions.py
├─ services.py
├─ tests.py
├─ urls.py
├─ views.py
├─ views_ia.py
├─ __init__.py
├─ forms_template/
│  ├─ accidente.py · buscar_accidente.py · centro_trabajo.py · declaracion.py · document.py · empresa.py · home.py · trabajador.py
│  └─ __init__.py
├─ migrations/                     — 0001_initial.py ... 0014_accidentes_resumen.py
├─ setting/
│  ├─ data/data.json
│  └─ prompt/prompt.json
├─ static/accidentes/
│  ├─ css/ (arbol.css, base.css, buscar_accidente.css, datos_*.css, declaraciones.css, fotos_documentos.css,
│  │        generar_informe.css, hechos.css, home.css, login.css, medidas_correctivas.css, notification.css, policies.css, progress.css, relato.css)
│  └─ img/ (favicon-ist.ico/png, favicon.ico, logo_ist.png)
├─ templates/accidentes/
│  ├─ arbol.html · base.html · buscar_accidente.html · datos_accidente.html · datos_empresa.html · datos_trabajador.html
│  │  declaraciones.html · fotos_documentos.html · generar_informe.html · hechos.html · home.html · medidas_correctivas.html · notification.html · relato.html
│  ├─ compliance/ (ley_21459.html · ley_21663.html · ley_21719.html · policies.html)
│  ├─ includes/ (disclaimer.html · progress_bar.html · sidebar.html)
│  └─ partials/
│     ├─ accidente/form_accidente.html
│     ├─ arbol/_arbol_partial.html
│     ├─ docs/_doc_card.html
│     ├─ empresa/(campo_centro_id.html · campo_direccion.html · form_empresa.html · opciones_comunas.html · opciones_nombres.html)
│     ├─ entrevistas/(_add_new_response.html · _badges_oob.html · _declaraciones_wrapper.html · _grid_oob.html · _pregunta_card.html)
│     ├─ hechos/_hechos_wrapper.html
│     ├─ home/(cards.html · table.html)
│     ├─ medidas/_medidas_wrapper.html
│     └─ relato/_relato_wrapper.html
├─ utils/
│  ├─ causal_tree.py · change_detector.py · crear_informe_doc.py · demo_storage.py · mixins.py · notification.py · progress.py · prompts.py · reportes.py · restored_doc.py
└─ views_api/
   ├─ arbol.py · declaraciones.py · fotos_documentos.py · generar_informe.py · hechos.py · medidas_correctivas.py · prompt_utils.py · relato.py
```

**Función de cada archivo (explicativo):**

- `access.py` — utilidades de **autorización/control de acceso** (validaciones de permisos por rol/caso).
- `admin.py` — registro de **ModelAdmin** para la app.
- `apps.py` — configuración de la app (Django `AppConfig`).
- `carga_datos_json.py` — rutina para **migrar/cargar datos demo** desde `setting/data/data.json` (usada en bootstrap/entrypoint).
- `context_processor(s).py` — inyección de **variables globales** a plantillas (flags, branding, user info).
- `decorators.py` — **decoradores** de vistas (roles, restricciones HTMX, ownership).
- `forms.py` — **formularios** de alto nivel (búsqueda, edición de accidente, medidas, etc.); los específicos por pantalla están en `forms_template/`.
- `managers.py` — **QuerySets/Managers** personalizados (consultas frecuentes).
- `models.py` — **modelos** del dominio (Accidente, Empresa, Trabajador, Declaración, Hechos, Documentos, Medidas, etc.).
- `permissions.py` — **reglas de permiso** reusables por vistas y servicios.
- `services.py` — **capa de servicios**: orquesta operaciones (crear caso, consolidar informe, adjuntar docs, etc.).
- `tests.py` — pruebas del módulo.
- `urls.py` — ruteo de la app.
- `views.py` — **vistas** principales (render de páginas, manejo de formularios).
- `views_ia.py` — vistas asociadas a **funcionalidades IA** (relato, árbol, medidas) basadas en `prompt/prompt.json`.
- `forms_template/*.py` — formularios especializados por pantalla (accidente, empresa, trabajador, declaraciones, búsqueda, etc.).
- `migrations/*.py` — cambios de esquema (creación/alteración de tablas/campos).
- `setting/data.json` — catálogos/datos de apoyo para formularios.
- `setting/prompt.json` — prompts versionados para IA (árbol, relato, preguntas, medidas).
- `static/accidentes/css/*.css` — estilos por página (coinciden con vistas/plantillas).
- `static/accidentes/img/*` — branding/icons.
- `templates/accidentes/*.html` — páginas del flujo (home, datos_*, entrevistas, documentos, relato, hechos, árbol, medidas, informe).
- `templates/accidentes/partials/*` — fragmentos reutilizables (cards, wrappers, forms).
- `utils/*.py` — utilidades del módulo (árbol causal, detección de cambios, generación de informe DOCX/PDF, mixins, notificaciones, progreso, prompts, reportes, restauración).
- `views_api/*.py` — endpoints internos por subflujo (arbol, declaraciones, hechos, relato, medidas, documentos, informe, prompts).

---

### adminpanel/

```text
adminpanel/
├─ admin.py
├─ apps.py
├─ forms.py
├─ mixins.py
├─ models.py
├─ permissions.py
├─ tests.py
├─ urls.py
├─ views.py
├─ __init__.py
├─ admin_function/
│  ├─ descargar_informe.py
│  └─ report_excel.py
├─ migrations/
│  └─ __init__.py
├─ static/adminpanel/css/
│  └─ adminpanel.css
├─ templates/adminpanel/
│  ├─ base_adminpanel.html
│  ├─ crear_investigacion.html
│  ├─ mis_investigaciones.html
│  ├─ report_excel.html
│  ├─ includes/
│  │  └─ sidebar.html
│  └─ partials/
│     ├─ crear/
│     │  ├─ _alerta_fuera_alcance.html
│     │  ├─ _empresa_select.html
│     │  ├─ _no_encontrado.html
│     │  ├─ _seleccionado.html
│     │  ├─ _seleccion_requerida.html
│     │  ├─ _trabajador_modal.html
│     │  ├─ _trabajador_panel_encontrado.html
│     │  ├─ _trabajador_panel_no_encontrado.html
│     │  ├─ _trabajador_panel_ok.html
│     │  ├─ _trabajador_panel_vacio.html
│     │  └─ _usuario_resultados.html
│     ├─ investigaciones_list/
│     │  └─ _mis_investigaciones_table.html
│     └─ report/
│        ├─ _filters.html
│        ├─ _preview.html
│        └─ _table.html
├─ templatetags/
│  ├─ adminpanel_extras.py
│  └─ __init__.py
└─ utils/
   ├─ access.py
   ├─ assignments.py
   └─ __init__.py
```

**Archivos raíz del panel**
- `admin.py` — Registro y personalización de modelos en **Django Admin** del panel (columnas, filtros, búsqueda).
- `apps.py` — Configuración `AppConfig` de la app.
- `forms.py` — Formularios del panel (crear investigación, filtros de reportes, búsquedas).
- `mixins.py` — Mixins reutilizables (paginación, permisos, helpers de contexto).
- `models.py` — Modelos que respaldan el panel (si aplica).
- `permissions.py` — Reglas de permisos específicas del panel (roles con acceso a crear/listar/exportar).
- `tests.py` — Tests de formularios/vistas/permiso.
- `urls.py` — Ruteo: crear investigación, mis investigaciones, reportes/export.
- `views.py` — Vistas (FBV/CBV) que renderizan templates y coordinan formularios/exports.
- `__init__.py` — Marca de paquete.

**admin_function/**
- `descargar_informe.py` — Genera/descarga el **informe** consolidado.
- `report_excel.py` — Construye **exportación a Excel** (listados/métricas).

**migrations/**
- `__init__.py` — Inicializa el paquete de migraciones del módulo.

**Estáticos**
- `static/adminpanel/css/adminpanel.css` — Estilos del panel (layout, tablas, formularios, parciales).

**Templates**
- `templates/adminpanel/base_adminpanel.html` — Layout base; incluye `includes/sidebar.html`.
- `templates/adminpanel/crear_investigacion.html` — Flujo de creación (usa parciales de `partials/crear/`).
- `templates/adminpanel/mis_investigaciones.html` — Listado propio; usa `partials/investigaciones_list/_mis_investigaciones_table.html`.
- `templates/adminpanel/report_excel.html` — Filtros/vista previa/descarga (usa `partials/report/`).

**Partials**
- `partials/crear/*` — Estados de selección y formularios: alertas, selección de empresa/centro, modales de trabajador y estados (_encontrado_, _no_encontrado_, _ok_, _vacío_) y resultados de usuarios.
- `partials/investigaciones_list/_mis_investigaciones_table.html` — Tabla reutilizable para “Mis Investigaciones”.
- `partials/report/*` — `_filters.html`, `_preview.html`, `_table.html` para filtrar/previsualizar/exportar.

**templatetags/**
- `adminpanel_extras.py` — Template tags/filters del panel (formato de estados, helpers de tablas/menús).

**utils/**
- `access.py` — Utilidades de **acceso/permiso** específicas del panel.
- `assignments.py` — Lógica de **asignación** (investigador ↔ investigación).

---

### accounts/

```text
accounts/
├─ admin.py · apps.py · backends.py · forms.py · models.py · tests.py · urls.py · views.py
├─ management/commands/ensure_superuser.py
├─ migrations/ (0001_initial.py, 0002_alter_user_rol.py, 0003_alter_user_rol.py)
└─ templates/registration/
   ├─ login.html
   ├─ password_reset_confirm_accounts.html · password_reset_complete_accounts.html · password_reset_done_accounts.html
   ├─ password_reset_email_accounts.html · password_reset_subject_accounts.txt
   └─ recuperar_pass.html
```

- Autenticación y gestión de usuarios, con **comando** para asegurar superusuario y **templates** de login/reset.

---

## Roles del Sistema

- **Administrador IST** (superadmin general)
- **Administrador Holding**
- **Administrador Empresa**
- **Investigador**
- **Investigador IST**

> Los permisos condicionan creación de casos, acceso a datos y descargas (p. ej., informes).

---

## Flujo de Uso (Guía de Usuario)

1. **Ingreso** (login con RUT y contraseña).  
2. **Home**: listado de casos asignados con resumen (empresa, datos clave).  
3. **Datos Empresa**: región, comuna, centro de trabajo (autocompletado, validaciones).  
4. **Datos Trabajador**: datos personales y **antigüedad** (empresa/cargo).  
5. **Datos Accidente**: fecha/hora, lugar, tipo/naturaleza de lesión, parte afectada, proceso y tarea.  
6. **Asistente de Entrevistas (IA)**: preguntas para accidentado, testigo y supervisor; editar/agregar/eliminar; guardar.  
7. **Fotos y Documentos**: subir o enlazar evidencias requeridas.  
8. **Relato (IA)**: genera relato inicial + preguntas de profundidad (actos inseguros, protocolos y políticas) → relato final editable.  
9. **Hechos del Accidente**: separar cronológicamente acciones; reordenar/agregar/eliminar.  
10. **Árbol de Causa (IA)**: generar, navegar y editar nodos/ramas; regenerar si hace falta.  
11. **Medidas Correctivas (IA)**: generar, editar y asignar responsables/fechas/especialidad/gravedad.  
12. **Generar Informe**: consolidar y descargar; versiones con historial recuperable.  

---

## Seguridad y Cumplimiento

- **Autenticación obligatoria** + **permisos por rol** (admin/admin_ist/admin_holding/admin_empresa/investigador).
- **Descargas protegidas** en `protected_media/` (p. ej., Nginx con X-Accel-Redirect para rutas internas).
- **Encabezados de seguridad**, saneamiento de nombres de archivo y **CSRF**.
- **Auditoría** de cambios por caso y control de acceso por jerarquía (holding/empresa).
- **Protección de datos** y buenas prácticas de ciberseguridad (captura de IP en firmas de políticas según normativa local).

---

## Configuración, Desarrollo y Scripts

### Requisitos
- Python 3.10+
- MySQL 8.x
- (Opcional) Docker/Docker Compose

### Setup local (modo rápido)
```bash
python -m venv .venv
source .venv/bin/activate    # (Windows: .venv\Scriptsctivate)
pip install -r requirements.txt

# variables de entorno (ejemplo)
export DJANGO_SETTINGS_MODULE=core.settings
export SECRET_KEY="cambia_esta_clave"
export DATABASE_URL="mysql://user:pass@localhost:3306/accidentes"

python manage.py migrate
python manage.py runserver
```

### Datos iniciales (opcional)
- `accidentes/carga_datos_json.py` puede utilizarse para **migrar datos** desde `setting/data/data.json` (según variable de entorno/entrypoint).

### Scripts útiles
```bash
python manage.py createsuperuser
python manage.py collectstatic
# (si aplica) python accidentes/carga_datos_json.py
```

---

## Despliegue (Docker Compose)

Ejemplo mínimo de comandos (el repo incluye `docker-compose*.yml`):

```bash
# Desarrollo
docker compose -f docker-compose-dev.yml up --build

# Producción/staging (ejemplo)
docker compose -f docker-compose.yml up -d
```

- Servicios: `web` (Django + Gunicorn), `db` (MySQL), `nginx` (proxy, descargas protegidas).
- Variables sensibles vía `.env` (no versionar).
- Estáticos en `static/` y media en `protected_media/` (montajes de volumen).

---

## Pruebas

```bash
python manage.py test
# o pytest si el repositorio lo incluye
```

Áreas a verificar: prompts IA (JSON válido), subida/descarga de archivos (extensión/tamaño), permisos y rutas, flujo completo end-to-end.

---

## Roadmap

- Mejoras UX en árbol causal y edición de medidas.
- Export adicional (PDF con plantilla institucional).
- Paneles de métricas (casos abiertos/cerrados, tiempos medios).
- Integración CI/CD con análisis estático y despliegue automatizado.

---

## Créditos

- Líder de Proyecto: **David Gonzalez**
- Desarrollo: **Agustín Lepe**, **David Ñanculeo**

---

> _Este README se genera a partir de la estructura real del repositorio y de la documentación funcional/técnica cargada. Para mantenerlo actualizado, conviene regenerar las secciones de árbol cuando cambie la estructura del proyecto._
