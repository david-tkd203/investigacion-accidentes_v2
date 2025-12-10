# -*- coding: utf-8 -*-
# Archivo generado automáticamente a partir de /mnt/data/ct-smu-demo.xlsx
# Contiene la lista COMPLETA de centros embebidos (sin depender del Excel).
# Se separa por la columna "Empresa" en el Excel:
#  - "RENDIC HERMANOS S.A." → CENTROS_RENDIC
#  - "SUPER 10 S.A."        → CENTROS_SUPER10
# Si aparece otra etiqueta, queda en UNMAPPED_DEBUG para diagnóstico.

from django.db import transaction
from django.contrib.auth import get_user_model
from accidentes.models import (
    Holdings, Empresas, CentrosTrabajo,
    Trabajadores, Accidentes, ArbolCausas, Declaraciones, Documentos,
    Hechos, Informes, PreguntasGuia, Prescripciones, AccidenteJsonData
)

User = get_user_model()

# ==============================
# LISTAS EMBEBIDAS DE CENTROS
# ==============================

# Centros para RENDIC HERMANOS S.A.
CENTROS_RENDIC = [
  {
    "nombre_local": "UNIMARC RECOVA LA SERENA",
    "direccion_centro": "Brasil 715",
    "region": "Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC ESTADO SANTIAGO",
    "direccion_centro": "Estado # 85",
    "region": "Metropolitana",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "UNIMARC TARAPACA ALTO HOSPICIO",
    "direccion_centro": "Ruta A16 3350",
    "region": "Región de Tarapacá",
    "comuna": "Alto Hospicio"
  },
  {
    "nombre_local": "UNIMARC BILBAO IQUIQUE",
    "direccion_centro": "Fco.Bilbao # 3545",
    "region": "Región de Tarapacá",
    "comuna": "Iquique"
  },
  {
    "nombre_local": "UNIMARC AMUNATEGUI IQUIQUE",
    "direccion_centro": "Amunategui # 902",
    "region": "Región de Tarapacá",
    "comuna": "Iquique"
  },
  {
    "nombre_local": "UNIMARC VIVAR IQUIQUE",
    "direccion_centro": "Vivar # 786",
    "region": "Región de Tarapacá",
    "comuna": "Iquique"
  },
  {
    "nombre_local": "UNIMARC IQUIQUE CENTRO TARAPACA",
    "direccion_centro": "Tarapaca # 579",
    "region": "Región de Tarapacá",
    "comuna": "Iquique"
  },
  {
    "nombre_local": "UNIMARC JUAN MARTINEZ IQUIQUE",
    "direccion_centro": "Manuel Rodriguez # 964",
    "region": "Región de Tarapacá",
    "comuna": "Iquique"
  },
  {
    "nombre_local": "UNIMARC LOS MOLLES IQUIQUE",
    "direccion_centro": "Santiago Polanco # 2251",
    "region": "Región de Tarapacá",
    "comuna": "Iquique"
  },
  {
    "nombre_local": "UNIMARC LA CHIMBA P.A.C.",
    "direccion_centro": "Pedro Aguirre Cerda #11387",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC LA TORRE ANTOFAGASTA",
    "direccion_centro": "Carlos Pezoa Veliz 10-22 Loc 01",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC CALAMA GRANADEROS",
    "direccion_centro": "Granaderos 3180",
    "region": "Región de Antofagasta",
    "comuna": "Calama"
  },
  {
    "nombre_local": "UNIMARC CALAMA ACONCAGUA",
    "direccion_centro": "Aconcagua 2588",
    "region": "Región de Antofagasta",
    "comuna": "Calama"
  },
  {
    "nombre_local": "UNIMARC GRAN VIA ANTOFAGASTA",
    "direccion_centro": "Avda. Angamos 0159",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC TOCOPILLA POLICARPO TORO",
    "direccion_centro": "Policarpo Toro S/N",
    "region": "Región de Antofagasta",
    "comuna": "Tocopilla"
  },
  {
    "nombre_local": "UNIMARC PLAZA ANTOFAGASTA",
    "direccion_centro": "Ignacio Carrera Pinto 909",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC COVIEFI ANTOFAGASTA",
    "direccion_centro": "Av. Argentina 1910",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC PAMPINO ANTOFAGASTA",
    "direccion_centro": "Av. Santos Ossa 2350",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC BONILLA ANTOFAGASTA",
    "direccion_centro": "Huamachuco 8481 (8484)",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC OVIEDO CAVADA ANTOFAGASTA",
    "direccion_centro": "Carlos Oviedo Cavada 5319",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC LA TORRE CALAMA",
    "direccion_centro": "Latorre 2149",
    "region": "Región de Antofagasta",
    "comuna": "Calama"
  },
  {
    "nombre_local": "UNIMARC LA CHIMBA ANTOFAGASTA",
    "direccion_centro": "Pedro Aguirre Cerda 8700",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC PARQUE ANTOFAGASTA",
    "direccion_centro": "Av. Jose Miguel Carrera 1527",
    "region": "Región de Antofagasta",
    "comuna": "Antofagasta"
  },
  {
    "nombre_local": "UNIMARC TOCOPILLA 21 DE MAYO",
    "direccion_centro": "21 De mayo 1704",
    "region": "Región de Antofagasta",
    "comuna": "Tocopilla"
  },
  {
    "nombre_local": "UNIMARC BRASILIA CALAMA",
    "direccion_centro": "Brasilia 2386",
    "region": "Región de Antofagasta",
    "comuna": "Calama"
  },
  {
    "nombre_local": "UNIMARC EL SALVADOR DIEGO ALMAGRO",
    "direccion_centro": "Ohiggins # 115",
    "region": "Región de Atacama",
    "comuna": "Diego De Almagro"
  },
  {
    "nombre_local": "UNIMARC LOS CARRERAS COPIAPO",
    "direccion_centro": "Los Carreras # 2242",
    "region": "Región de Atacama",
    "comuna": "Copiapó"
  },
  {
    "nombre_local": "UNIMARC VALLENAR ARTURO PRAT",
    "direccion_centro": "Arturo Prat # 2350",
    "region": "Región de Atacama",
    "comuna": "Vallenar"
  },
  {
    "nombre_local": "UNIMARC EL PALOMAR COPIAPO",
    "direccion_centro": "Av. Palomar # 1525",
    "region": "Región de Atacama",
    "comuna": "Copiapó"
  },
  {
    "nombre_local": "UNIMARC COPIAPO AV. HENRÍQUEZ",
    "direccion_centro": "Avda.Henrriquez # 523",
    "region": "Región de Atacama",
    "comuna": "Copiapó"
  },
  {
    "nombre_local": "UNIMARC CALDERA BATALLON ATACAMA",
    "direccion_centro": "Batallon Atacama # 319",
    "region": "Región de Atacama",
    "comuna": "Caldera"
  },
  {
    "nombre_local": "UNIMARC BARQUITO CHAÑARAL",
    "direccion_centro": "G Mistral 602L",
    "region": "Región de Atacama",
    "comuna": "Chañaral"
  },
  {
    "nombre_local": "UNIMARC VALLENAR BRASIL",
    "direccion_centro": "Brasil # 663",
    "region": "Región de Atacama",
    "comuna": "Vallenar"
  },
  {
    "nombre_local": "UNIMARC CHAÑARCILLO COPIAPO",
    "direccion_centro": "Chacabuco # 231",
    "region": "Región de Atacama",
    "comuna": "Copiapó"
  },
  {
    "nombre_local": "UNIMARC CHACABUCO COPIAPO",
    "direccion_centro": "Los Carreras # 586",
    "region": "Región de Atacama",
    "comuna": "Copiapó"
  },
  {
    "nombre_local": "UNIMARC LOS CARRERA COPIAPO",
    "direccion_centro": "Los Carreras # 479",
    "region": "Región de Atacama",
    "comuna": "Copiapó"
  },
  {
    "nombre_local": "UNIMARC COQUIMBO FCO. VARELA",
    "direccion_centro": "Varela 1480",
    "region": "Región de Coquimbo",
    "comuna": "Coquimbo"
  },
  {
    "nombre_local": "UNIMARC HUACHALALUME COQUIMBO",
    "direccion_centro": "Avenida Waldo Alcalde 401, Local #1",
    "region": "Región de Coquimbo",
    "comuna": "Coquimbo"
  },
  {
    "nombre_local": "UNIMARC LOS ALAMOS COQUIMBO",
    "direccion_centro": "Los Alamos 580",
    "region": "Región de Coquimbo",
    "comuna": "Coquimbo"
  },
  {
    "nombre_local": "UNIMARC RECOVA LA SERENA",
    "direccion_centro": "Brasil 715",
    "region": "Región de Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC TANGUE OVALLE",
    "direccion_centro": "Tangue 36",
    "region": "Región de Coquimbo",
    "comuna": "Ovalle"
  },
  {
    "nombre_local": "UNIMARC REGIMIENTO ARICA LA SERENA",
    "direccion_centro": "Regimiento Arica # 6001",
    "region": "Región de Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC SINDEMPART COQUIMBO",
    "direccion_centro": "Avda. El Sauce 981",
    "region": "Región de Coquimbo",
    "comuna": "Coquimbo"
  },
  {
    "nombre_local": "UNIMARC ALTO PEÑUELAS COQUIMBO",
    "direccion_centro": "Alessandri 531",
    "region": "Región de Coquimbo",
    "comuna": "Coquimbo"
  },
  {
    "nombre_local": "UNIMARC CISTERNAS LA SERENA",
    "direccion_centro": "Reinaldo Boltz 1950",
    "region": "Región de Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC SALAMANCA BULNES",
    "direccion_centro": "Bulnes 220",
    "region": "Región de Coquimbo",
    "comuna": "Salamanca"
  },
  {
    "nombre_local": "UNIMARC LOS VILOS CAUPOLICAN",
    "direccion_centro": "Caupolican 584",
    "region": "Región de Coquimbo",
    "comuna": "Los Vilos"
  },
  {
    "nombre_local": "UNIMARC ILLAPEL CONSTITUCION",
    "direccion_centro": "Constitucion 515",
    "region": "Región de Coquimbo",
    "comuna": "Illapel"
  },
  {
    "nombre_local": "UNIMARC SALAMANCA RUZ VALLEDOR",
    "direccion_centro": "Manuel Bulnes 677",
    "region": "Región de Coquimbo",
    "comuna": "Salamanca"
  },
  {
    "nombre_local": "UNIMARC BENAVENTE OVALLE",
    "direccion_centro": "Benavente 221",
    "region": "Región de Coquimbo",
    "comuna": "Ovalle"
  },
  {
    "nombre_local": "UNIMARC OVALLE LIBERTAD",
    "direccion_centro": "Libertad 249",
    "region": "Región de Coquimbo",
    "comuna": "Ovalle"
  },
  {
    "nombre_local": "UNIMARC FLORIDA LA SERENA",
    "direccion_centro": "Av.18 De Septiembre/Las Parcelas 5040",
    "region": "Región de Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC BALMACEDA LA SERENA",
    "direccion_centro": "Balmaceda 1350",
    "region": "Región de Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC VICUÑA CHACABUCO",
    "direccion_centro": "Chacabuco 302",
    "region": "Región de Coquimbo",
    "comuna": "Vicuña"
  },
  {
    "nombre_local": "UNIMARC EL MILAGRO LA SERENA",
    "direccion_centro": "Santiago Apostol 4063",
    "region": "Región de Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC LAS COMPAÑIAS LA SERENA",
    "direccion_centro": "Nicaragua 1571",
    "region": "Región de Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC COMBARBALA COMERCIO",
    "direccion_centro": "Comercio 310",
    "region": "Región de Coquimbo",
    "comuna": "Combarbalá"
  },
  {
    "nombre_local": "UNIMARC ILLAPEL INDEPENDENCIA",
    "direccion_centro": "Independencia 0104",
    "region": "Región de Coquimbo",
    "comuna": "Illapel"
  },
  {
    "nombre_local": "UNIMARC CIRCUNVALACION LA SERENA",
    "direccion_centro": "Av. Monjitas Oriente 2706",
    "region": "Región de Coquimbo",
    "comuna": "La Serena"
  },
  {
    "nombre_local": "UNIMARC 4 PONIENTE VIÑA DEL MAR",
    "direccion_centro": "4 Poniente # 630",
    "region": "Región de Valparaíso",
    "comuna": "Viña Del Mar"
  },
  {
    "nombre_local": "UNIMARC EL QUISCO JOSE NARCIZO",
    "direccion_centro": "Jose Narciso Aguirre # 29",
    "region": "Región de Valparaíso",
    "comuna": "El Quisco"
  },
  {
    "nombre_local": "UNIMARC J. DEL MAR VIÑA DEL MAR",
    "direccion_centro": "Los Sargazos # 1855",
    "region": "Región de Valparaíso",
    "comuna": "Viña Del Mar"
  },
  {
    "nombre_local": "UNIMARC LLAY LLAY BALMACEDA",
    "direccion_centro": "Balmaceda # 307",
    "region": "Región de Valparaíso",
    "comuna": "Llay-Llay"
  },
  {
    "nombre_local": "UNIMARC LOS ANDES HERMANOS CLARK",
    "direccion_centro": "Hermanos Clark 55",
    "region": "Región de Valparaíso",
    "comuna": "Los Andes"
  },
  {
    "nombre_local": "UNIMARC LOS ANDES YERBAS BUENAS",
    "direccion_centro": "Yerbas Buenas # 460",
    "region": "Región de Valparaíso",
    "comuna": "Los Andes"
  },
  {
    "nombre_local": "UNIMARC SAN ESTEBAN ALESSANDRI",
    "direccion_centro": "Avenida Arturo Alessandri Palma 50",
    "region": "Región de Valparaíso",
    "comuna": "San Esteban"
  },
  {
    "nombre_local": "UNIMARC SANTO DGO CASAS DE LA BOCA",
    "direccion_centro": "Ruta 66, Esquina Casas de la Boca s/n",
    "region": "Región de Valparaíso",
    "comuna": "Santo Domingo"
  },
  {
    "nombre_local": "UNIMARC CASABLANCA CONSTITUCION",
    "direccion_centro": "Constitucion # 120",
    "region": "Región de Valparaíso",
    "comuna": "Casablanca"
  },
  {
    "nombre_local": "UNIMARC EL TABO SAN MARCOS",
    "direccion_centro": "San Marcos # 1027",
    "region": "Región de Valparaíso",
    "comuna": "El Tabo"
  },
  {
    "nombre_local": "UNIMARC SAN FELIPE PORTUS",
    "direccion_centro": "Portus # 1248",
    "region": "Región de Valparaíso",
    "comuna": "San Felipe"
  },
  {
    "nombre_local": "UNIMARC VALPARAISO ERRAZURIZ",
    "direccion_centro": "Av. Errazuriz # 629 (Puerto)",
    "region": "Región de Valparaíso",
    "comuna": "Valparaíso"
  },
  {
    "nombre_local": "UNIMARC LIMACHE REPUBLICA",
    "direccion_centro": "República # 342",
    "region": "Región de Valparaíso",
    "comuna": "Limache"
  },
  {
    "nombre_local": "UNIMARC QUINTERO NORMANDIE",
    "direccion_centro": "Avda.Normandie # 2680",
    "region": "Región de Valparaíso",
    "comuna": "Quintero"
  },
  {
    "nombre_local": "UNIMARC PUCHUNCAVI PDTE. RIOS",
    "direccion_centro": "Avda Presidente Rios # 672",
    "region": "Región de Valparaíso",
    "comuna": "Puchuncaví"
  },
  {
    "nombre_local": "UNIMARC SAN FELIPE ENCON",
    "direccion_centro": "Encon 500",
    "region": "Región de Valparaíso",
    "comuna": "San Felipe"
  },
  {
    "nombre_local": "UNIMARC CARTAGENA CASANOVA",
    "direccion_centro": "Avda.Arzobispo Casanova # 306",
    "region": "Región de Valparaíso",
    "comuna": "Cartagena"
  },
  {
    "nombre_local": "UNIMARC QUILLOTA O'HIGGINS",
    "direccion_centro": "O'Higgins # 34",
    "region": "Región de Valparaíso",
    "comuna": "Quillota"
  },
  {
    "nombre_local": "UNIMARC CURAUMA VALAPARAISO",
    "direccion_centro": "Obispo Valdes # 1170",
    "region": "Región de Valparaíso",
    "comuna": "Valparaíso"
  },
  {
    "nombre_local": "UNIMARC OLMUE DIEGO PORTALES",
    "direccion_centro": "Diego Portales # 2090",
    "region": "Región de Valparaíso",
    "comuna": "Olmué"
  },
  {
    "nombre_local": "UNIMARC VILLA ALEMANA VALPARAISO",
    "direccion_centro": "Av. Valparaíso # 1982",
    "region": "Región de Valparaíso",
    "comuna": "Villa Alemana"
  },
  {
    "nombre_local": "UNIMARC VILLA ALEMANA ARRIETA",
    "direccion_centro": "Av.Valparaiso # 899",
    "region": "Región de Valparaíso",
    "comuna": "Villa Alemana"
  },
  {
    "nombre_local": "UNIMARC SANTO DOMINGO EL GOLF",
    "direccion_centro": "Avenida El Golf # 06",
    "region": "Región de Valparaíso",
    "comuna": "Santo Domingo"
  },
  {
    "nombre_local": "UNIMARC MAGA MARGA QUILPUE",
    "direccion_centro": "Del Alheli # 2011",
    "region": "Región de Valparaíso",
    "comuna": "Quilpué"
  },
  {
    "nombre_local": "UNIMARC ETCHEVERS VIÑA DEL MAR",
    "direccion_centro": "Etchevers Alto # 594",
    "region": "Región de Valparaíso",
    "comuna": "Viña Del Mar"
  },
  {
    "nombre_local": "UNIMARC 1 NORTE VIÑA DEL MAR",
    "direccion_centro": "1 Norte # 839",
    "region": "Región de Valparaíso",
    "comuna": "Viña Del Mar"
  },
  {
    "nombre_local": "UNIMARC QUINTERO ESTRELLA DE CHILE",
    "direccion_centro": "Estrella De Chile # 169",
    "region": "Región de Valparaíso",
    "comuna": "Quintero"
  },
  {
    "nombre_local": "UNIMARC LAS CABRAS J. MIG. CARRERA",
    "direccion_centro": "Jose Miguel Carrera 325",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Las Cabras"
  },
  {
    "nombre_local": "UNIMARC MEMBRILLAR RANCAGUA",
    "direccion_centro": "Membrillar N° 10",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Rancagua"
  },
  {
    "nombre_local": "UNIMARC MACHALI RANCAGUA",
    "direccion_centro": "Av. Miguel Ramirez N° 1420",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Rancagua"
  },
  {
    "nombre_local": "UNIMARC NANCAGUA ARMANDO JARAMILLO",
    "direccion_centro": "Armando Jaramillo N°152",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Nancagua"
  },
  {
    "nombre_local": "UNIMARC RANCAGUA KENNEDY",
    "direccion_centro": "Av. Kennedy 2235",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Rancagua"
  },
  {
    "nombre_local": "UNIMARC CHIMBARONGO CARMEN LIRA",
    "direccion_centro": "Carmen Larrain 44",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Chimbarongo"
  },
  {
    "nombre_local": "UNIMARC SAN FERNANDO MAN.RODRÍGUEZ",
    "direccion_centro": "Manuel Rodriguez N°954",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "San Fernando"
  },
  {
    "nombre_local": "UNIMARC RANCAGUA DOCTOR SALINAS",
    "direccion_centro": "Doctor Salinas 115 Rancagua",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Rancagua"
  },
  {
    "nombre_local": "UNIMARC CHIMBARONGO GARCIA Y REYES",
    "direccion_centro": "Garcia Y Reyes S/N",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Chimbarongo"
  },
  {
    "nombre_local": "UNIMARC GRANEROS OBISPO RAFAEL",
    "direccion_centro": "Obispo Rafael Lira Infante 042",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Graneros"
  },
  {
    "nombre_local": "UNIMARC SAN JUAN DE MACHALI",
    "direccion_centro": "San Juan 1135 local 38 Machali",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Machali"
  },
  {
    "nombre_local": "UNIMARC PEUMO SARMIENTO",
    "direccion_centro": "Sarmiento 393",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Peumo"
  },
  {
    "nombre_local": "UNIMARC SAN FERNANDO O'HIGGINS",
    "direccion_centro": "Av. Bernardo Ohiggins 701",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "San Fernando"
  },
  {
    "nombre_local": "UNIMARC RANCAGUA REPUBLICA",
    "direccion_centro": "Republica De Chile 391",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Rancagua"
  },
  {
    "nombre_local": "UNIMARC CAMILO HENRIQUEZ O'HIGGINS",
    "direccion_centro": "Avd. Camilo Henriquez 655 Curico",
    "region": "Región del Maule",
    "comuna": "Curicó"
  },
  {
    "nombre_local": "UNIMARC CAMILO HENRIQUEZ YUNGAY",
    "direccion_centro": "Avd. Camilo Henriquez 445 Curico",
    "region": "Región del Maule",
    "comuna": "Curicó"
  },
  {
    "nombre_local": "UNIMARC LONTUE MOLINA",
    "direccion_centro": "Avda.7 Abril 2069 Lontue",
    "region": "Región del Maule",
    "comuna": "Molina"
  },
  {
    "nombre_local": "UNIMARC AV ESPAÑA CURICO",
    "direccion_centro": "Avda España 414",
    "region": "Región del Maule",
    "comuna": "Curicó"
  },
  {
    "nombre_local": "UNIMARC SAN CLEMENTE HUAMACHUCO",
    "direccion_centro": "Huamachuco # 613 San Clemente",
    "region": "Región del Maule",
    "comuna": "San Clemente"
  },
  {
    "nombre_local": "UNIMARC TALCA CARLOS SCHORR",
    "direccion_centro": "Avda Carlos Schorr N°265",
    "region": "Región del Maule",
    "comuna": "Talca"
  },
  {
    "nombre_local": "UNIMARC TENO AVDA. COMALLE",
    "direccion_centro": "Avda. Comalle Nº 50",
    "region": "Región del Maule",
    "comuna": "Teno"
  },
  {
    "nombre_local": "UNIMARC CURICO ALEMEDA",
    "direccion_centro": "Estado 43",
    "region": "Región del Maule",
    "comuna": "Curicó"
  },
  {
    "nombre_local": "UNIMARC CURICO TERMINAL",
    "direccion_centro": "Prat 733 Curico",
    "region": "Región del Maule",
    "comuna": "Curicó"
  },
  {
    "nombre_local": "UNIMARC TALCA 14 SUR",
    "direccion_centro": "14 Sur 1310 Talca",
    "region": "Región del Maule",
    "comuna": "Talca"
  },
  {
    "nombre_local": "UNIMARC MOLINA LUIS CRUZ MARTINEZ",
    "direccion_centro": "Avda. Luis Cruz Martinez 1314, Molina",
    "region": "Región del Maule",
    "comuna": "Molina"
  },
  {
    "nombre_local": "UNIMARC CONSTITUCION VIAL",
    "direccion_centro": "Vial 224",
    "region": "Región del Maule",
    "comuna": "Constitución"
  },
  {
    "nombre_local": "UNIMARC SAN JAVIER BALMACEDA",
    "direccion_centro": "Balmaceda 1900",
    "region": "Región del Maule",
    "comuna": "San Javier"
  },
  {
    "nombre_local": "UNIMARC ROMERAL LIBERTAD",
    "direccion_centro": "Av. Libertad 1124 B Romeral",
    "region": "Región del Maule",
    "comuna": "Romeral"
  },
  {
    "nombre_local": "UNIMARC MOLINA ARTURO PRATT",
    "direccion_centro": "Av. Luis Cruz Martínez #2016",
    "region": "Región del Maule",
    "comuna": "Molina"
  },
  {
    "nombre_local": "UNIMARC CAUQUENES CATEDRAL",
    "direccion_centro": "Catedral 215 Cauquenes",
    "region": "Región del Maule",
    "comuna": "Cauquenes"
  },
  {
    "nombre_local": "UNIMARC SAGRADA FAMILIA AV ESPERAN",
    "direccion_centro": "Avenida Esperanzanº 138 S.Familia",
    "region": "Región del Maule",
    "comuna": "Sagrada Familia"
  },
  {
    "nombre_local": "UNIMARC TALCA 1 NORTE",
    "direccion_centro": "Calle 1 Norte # 1570",
    "region": "Región del Maule",
    "comuna": "Talca"
  },
  {
    "nombre_local": "UNIMARC TALCA 2 SUR",
    "direccion_centro": "2 Sur 1953 Talca",
    "region": "Región del Maule",
    "comuna": "Talca"
  },
  {
    "nombre_local": "UNIMARC LINARES MAIPU",
    "direccion_centro": "Maipu Nº 556",
    "region": "Región del Maule",
    "comuna": "Linares"
  },
  {
    "nombre_local": "UNIMARC TALCA 5 NORTE",
    "direccion_centro": "Avenida 5 Norte N°3615",
    "region": "Región del Maule",
    "comuna": "Talca"
  },
  {
    "nombre_local": "UNIMARC CORONEL FREIRE",
    "direccion_centro": "M. Montt # 501",
    "region": "Región del Biobío",
    "comuna": "Coronel"
  },
  {
    "nombre_local": "UNIMARC COVADONGA ARAUCO",
    "direccion_centro": "Covadonga # 391 Arauco",
    "region": "Región del Biobío",
    "comuna": "Arauco"
  },
  {
    "nombre_local": "UNIMARC CURANILAHUE O'HIGGINS",
    "direccion_centro": "O'Higgins # 101",
    "region": "Región del Biobío",
    "comuna": "Curanilahue"
  },
  {
    "nombre_local": "UNIMARC GRAL CRUZ CABRERO",
    "direccion_centro": "General Cruz # 380 Cabrero",
    "region": "Región del Biobío",
    "comuna": "Cabrero"
  },
  {
    "nombre_local": "UNIMARC LEBU BULNES",
    "direccion_centro": "Bulnes # 130 Lebu",
    "region": "Región del Biobío",
    "comuna": "Lebu"
  },
  {
    "nombre_local": "UNIMARC LOS ANGELES CARRERA",
    "direccion_centro": "Los Carrera # 1380 Los Angeles",
    "region": "Región del Biobío",
    "comuna": "Los Angeles"
  },
  {
    "nombre_local": "UNIMARC COLON LOS ANGELES",
    "direccion_centro": "Colon # 600 Los Angeles",
    "region": "Región del Biobío",
    "comuna": "Los Angeles"
  },
  {
    "nombre_local": "UNIMARC LOTA P.A.C.",
    "direccion_centro": "Pedro Aguirre Cerda # 684 Lota",
    "region": "Región del Biobío",
    "comuna": "Lota"
  },
  {
    "nombre_local": "UNIMARC TALCAHUANO BILBAO",
    "direccion_centro": "Bilbao # 446",
    "region": "Región del Biobío",
    "comuna": "Talcahuano"
  },
  {
    "nombre_local": "UNIMARC MULCHEN ANIBAL PINTO",
    "direccion_centro": "Anibal Pinto # 777",
    "region": "Región del Biobío",
    "comuna": "Mulchén"
  },
  {
    "nombre_local": "UNIMARC MANQUIMAVIDA CHIGUAYANTE",
    "direccion_centro": "Manuel Rodriguez # 1500 Chiguayante",
    "region": "Región del Biobío",
    "comuna": "Chiguayante"
  },
  {
    "nombre_local": "UNIMARC EL VOLCAN CORONEL",
    "direccion_centro": "Juan Antonio Ríos # 3039",
    "region": "Región del Biobío",
    "comuna": "Coronel"
  },
  {
    "nombre_local": "UNIMARC CONCEPCION TUCAPEL",
    "direccion_centro": "Tucapel 1313",
    "region": "Región del Biobío",
    "comuna": "Concepción"
  },
  {
    "nombre_local": "UNIMARC HUALQUI LA ARAUCANA",
    "direccion_centro": "La Araucana # 490",
    "region": "Región del Biobío",
    "comuna": "Hualqui"
  },
  {
    "nombre_local": "UNIMARC PEÑUELAS HUALPEN",
    "direccion_centro": "Av. Dos 35",
    "region": "Región del Biobío",
    "comuna": "Hualpén"
  },
  {
    "nombre_local": "UNIMARC HUEPIL TUCAPEL",
    "direccion_centro": "Arturo Prat # 500 Huepil",
    "region": "Región del Biobío",
    "comuna": "Tucapel"
  },
  {
    "nombre_local": "UNIMARC LOMAS COLORADAS SAN PEDRO",
    "direccion_centro": "Los Mañíos # 7045 San Pedro De La Paz",
    "region": "Región del Biobío",
    "comuna": "San Pedro De La Paz"
  },
  {
    "nombre_local": "UNIMARC MARCONI LOS ANGELES",
    "direccion_centro": "Marconi # 1177",
    "region": "Región del Biobío",
    "comuna": "Los Angeles"
  },
  {
    "nombre_local": "UNIMARC HUALPEN BULGARIA",
    "direccion_centro": "Bulgaria 2818",
    "region": "Región del Biobío",
    "comuna": "Hualpén"
  },
  {
    "nombre_local": "UNIMARC CORONEL MANUEL MONTT",
    "direccion_centro": "Manuel Montt # 398",
    "region": "Región del Biobío",
    "comuna": "Coronel"
  },
  {
    "nombre_local": "UNIMARC BELLAVISTA CONCEPCION",
    "direccion_centro": "Lleuqe 1540",
    "region": "Región del Biobío",
    "comuna": "Concepción"
  },
  {
    "nombre_local": "UNIMARC HIGUERAS TALCAHUANO",
    "direccion_centro": "Las Araucarias 295",
    "region": "Región del Biobío",
    "comuna": "Talcahuano"
  },
  {
    "nombre_local": "UNIMARC CONCEPCION CHACABUCO",
    "direccion_centro": "Chacabuco 70",
    "region": "Región del Biobío",
    "comuna": "Concepción"
  },
  {
    "nombre_local": "UNIMARC LOMAS DE SAN ANDRES CONCEP",
    "direccion_centro": "Cosme Churruca 75 Local 21",
    "region": "Región del Biobío",
    "comuna": "Concepción"
  },
  {
    "nombre_local": "UNIMARC PORTAL LOS ANGELES",
    "direccion_centro": "Avenida Alemania # 100",
    "region": "Región del Biobío",
    "comuna": "Los Angeles"
  },
  {
    "nombre_local": "UNIMARC NACIMIENTO SAN MARTIN",
    "direccion_centro": "San Martín # 560",
    "region": "Región del Biobío",
    "comuna": "Nacimiento"
  },
  {
    "nombre_local": "UNIMARC CHIGUAYANTE 8 ORIENTE",
    "direccion_centro": "Av 8 Oriente # 720",
    "region": "Región del Biobío",
    "comuna": "Chiguayante"
  },
  {
    "nombre_local": "UNIMARC LOS LLEUQUES CAÑETE",
    "direccion_centro": "Avda. Pdte. Eduardo Frei # 162 Cañete",
    "region": "Región del Biobío",
    "comuna": "Cañete"
  },
  {
    "nombre_local": "UNIMARC CORONEL LAUTARO",
    "direccion_centro": "Lautaro # 477",
    "region": "Región del Biobío",
    "comuna": "Coronel"
  },
  {
    "nombre_local": "UNIMARC LA VIOLETA LOTA",
    "direccion_centro": "Pedro Aguirre Cerda # 602 Lota",
    "region": "Región del Biobío",
    "comuna": "Lota"
  },
  {
    "nombre_local": "UNIMARC LOS HUERTOS SAN PEDRO",
    "direccion_centro": "Las Violetas 1782, Huertos Familiares",
    "region": "Región del Biobío",
    "comuna": "San Pedro De La Paz"
  },
  {
    "nombre_local": "UNIMARC PENCO FREIRE",
    "direccion_centro": "Freire 699",
    "region": "Región del Biobío",
    "comuna": "Penco"
  },
  {
    "nombre_local": "UNIMARC GOMEZ CARREÑO TALCAHUANO",
    "direccion_centro": "Gomez Carreño 3875",
    "region": "Región del Biobío",
    "comuna": "Talcahuano"
  },
  {
    "nombre_local": "UNIMARC CARACOL TOME",
    "direccion_centro": "Ignacio Serrano 980",
    "region": "Región del Biobío",
    "comuna": "Tomé"
  },
  {
    "nombre_local": "UNIMARC SAN PEDRO DEL MAR TUCAPEL",
    "direccion_centro": "Tucapel # 285",
    "region": "Región del Biobío",
    "comuna": "San Pedro De La Paz"
  },
  {
    "nombre_local": "UNIMARC CAÑETE SAAVEDRA",
    "direccion_centro": "Saavedra # 525 Cañete",
    "region": "Región del Biobío",
    "comuna": "Cañete"
  },
  {
    "nombre_local": "UNIMARC S.PEDRO DE LA PAZ EL VENAD",
    "direccion_centro": "Camino El Venado 1380",
    "region": "Región del Biobío",
    "comuna": "San Pedro De La Paz"
  },
  {
    "nombre_local": "UNIMARC YUMBEL O'HIGGINS",
    "direccion_centro": "O'Higgins # 620",
    "region": "Región del Biobío",
    "comuna": "Yumbel"
  },
  {
    "nombre_local": "UNIMARC LAJA BALMACEDA",
    "direccion_centro": "Balmaceda # 62 Laja",
    "region": "Región del Biobío",
    "comuna": "Laja"
  },
  {
    "nombre_local": "UNIMARC BARRIO INGLES TEMUCO",
    "direccion_centro": "Avenida Las Encinas # 02690",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "UNIMARC LONCOCHE BALMACEDA",
    "direccion_centro": "Balmaceda N° 389",
    "region": "Región de La Araucanía",
    "comuna": "Loncoche"
  },
  {
    "nombre_local": "UNIMARC OHIGGINS ANGOL",
    "direccion_centro": "Avenida O'Higgins N° 1257",
    "region": "Región de La Araucanía",
    "comuna": "Angol"
  },
  {
    "nombre_local": "UNIMARC COLLUPULLI CRUZ",
    "direccion_centro": "Cruz N° 233",
    "region": "Región de La Araucanía",
    "comuna": "Collipulli"
  },
  {
    "nombre_local": "UNIMARC CURACAUTIN O'HIGGINS",
    "direccion_centro": "Bernardo O'Higgins N° 515",
    "region": "Región de La Araucanía",
    "comuna": "Curacautín"
  },
  {
    "nombre_local": "UNIMARC PADRE LAS CASAS MANQUEHUE",
    "direccion_centro": "Maquehue N° 1244",
    "region": "Región de La Araucanía",
    "comuna": "Padre Las Casas"
  },
  {
    "nombre_local": "UNIMARC TRAIGUEN SANTA CRUZ",
    "direccion_centro": "Santa Cruz # 1170",
    "region": "Región de La Araucanía",
    "comuna": "Traiguén"
  },
  {
    "nombre_local": "UNIMARC LAUTARO O'HIGGINS",
    "direccion_centro": "Bernardo O'Higgins N°630",
    "region": "Región de La Araucanía",
    "comuna": "Lautaro"
  },
  {
    "nombre_local": "UNIMARC NUEVA IMPERIAL ARTURO PRAT",
    "direccion_centro": "Arturo Prat N° 246",
    "region": "Región de La Araucanía",
    "comuna": "Nueva Imperial"
  },
  {
    "nombre_local": "UNIMARC TEMUCO SAN MARTIN",
    "direccion_centro": "San Martin N° 0675",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "UNIMARC PUCON O'HIGGINS",
    "direccion_centro": "Avenida Bernardo O´Higgins # 774",
    "region": "Región de La Araucanía",
    "comuna": "Pucón"
  },
  {
    "nombre_local": "UNIMARC VILLARRICA GER.DE ALDERETE",
    "direccion_centro": "Geronimo De Alderete # 697",
    "region": "Región de La Araucanía",
    "comuna": "Villarrica"
  },
  {
    "nombre_local": "UNIMARC TEMUCO ALEMANIA",
    "direccion_centro": "Avenida Alemania # 849",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "UNIMARC TEMUCO ANIBAL PINTO",
    "direccion_centro": "Anibal Pinto # 72",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "UNIMARC TEMUCO CAUPOLICAN",
    "direccion_centro": "Avenida Caupolican # 0191",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "UNIMARC PITRUFQUEN BILBAO",
    "direccion_centro": "Bilbao # 476",
    "region": "Región de La Araucanía",
    "comuna": "Pitrufquén"
  },
  {
    "nombre_local": "UNIMARC VICTORIA PISAGUA",
    "direccion_centro": "Pisagua # 1354",
    "region": "Región de La Araucanía",
    "comuna": "Victoria"
  },
  {
    "nombre_local": "UNIMARC TEMUCO JAVIERA CARRERA",
    "direccion_centro": "Avenida Javiera Carrera # 1610",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "UNIMARC COLO COLO ANCUD",
    "direccion_centro": "Colo - Colo 318",
    "region": "Región de Los Lagos",
    "comuna": "Ancud"
  },
  {
    "nombre_local": "UNIMARC DALCAHUE",
    "direccion_centro": "Ramon Freire Poniente 625",
    "region": "Región de Los Lagos",
    "comuna": "Dalcahue"
  },
  {
    "nombre_local": "UNIMARC PUERTO MONTT TEPUAL",
    "direccion_centro": "Avenida El Tepual N° 1360",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC RAMIREZ OSORNO",
    "direccion_centro": "Ramirez # 699",
    "region": "Región de Los Lagos",
    "comuna": "Osorno"
  },
  {
    "nombre_local": "UNIMARC ROTONDA PUERTO MONTT",
    "direccion_centro": "Avenida Parque Industrial # 450",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC QUELLON LADRILLEROS",
    "direccion_centro": "Ladrillero # 460",
    "region": "Región de Los Lagos",
    "comuna": "Quellón"
  },
  {
    "nombre_local": "UNIMARC ACHAO QUINCHAO",
    "direccion_centro": "Delicias 06",
    "region": "Región de Los Lagos",
    "comuna": "Quinchao"
  },
  {
    "nombre_local": "UNIMARC CENTRAL OSORNO",
    "direccion_centro": "Patricio Lynch N° 1278",
    "region": "Región de Los Lagos",
    "comuna": "Osorno"
  },
  {
    "nombre_local": "UNIMARC OSORNO FRANCIA ZENTENO",
    "direccion_centro": "AV. Francia 1701 Local 1, Osorno",
    "region": "Región de Los Lagos",
    "comuna": "Osorno"
  },
  {
    "nombre_local": "UNIMARC LOS VOLCANES PUERTO MONTT",
    "direccion_centro": "Volcan Hornnopiren #1728",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC LOS NOTROS PUERTO MONTT",
    "direccion_centro": "Av Los Notros # 1272",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC ORIENTE OSORNO",
    "direccion_centro": "Julio Buschman # 2223",
    "region": "Región de Los Lagos",
    "comuna": "Osorno"
  },
  {
    "nombre_local": "UNIMARC JUAN SOLER PUERTO MONTT",
    "direccion_centro": "Juan Soler Manfredini 51",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC PALOMA PUERTO MONTT",
    "direccion_centro": "Volcan Puntiagudo # 100",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC PURRANQUE ELEUTER. RAMIREZ",
    "direccion_centro": "Eleuterio Ramirez N° 549",
    "region": "Región de Los Lagos",
    "comuna": "Purranque"
  },
  {
    "nombre_local": "UNIMARC ALERCE 2 PTO MONTT",
    "direccion_centro": "Avda Gabriela Mistral # 900",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC MIRASOL PUERTO MONTT",
    "direccion_centro": "Av De La Cruz 2006",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC CALBUCO ANTONIO VARAS",
    "direccion_centro": "Federico Errazuriz 572",
    "region": "Región de Los Lagos",
    "comuna": "Calbuco"
  },
  {
    "nombre_local": "UNIMARC URMENETA PUERTO MONTT",
    "direccion_centro": "Urmeneta 574",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC LOS MUERMOS PUERTO MONTT",
    "direccion_centro": "Padre Nelson Aguilar N 480, Local 1, Localidad Los Muermos",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC VICTORIA OSORNO",
    "direccion_centro": "Victoria N° 367",
    "region": "Región de Los Lagos",
    "comuna": "Osorno"
  },
  {
    "nombre_local": "UNIMARC FRUTILLAR ART. ALESSANDRI",
    "direccion_centro": "Arturo Alessandri # 381",
    "region": "Región de Los Lagos",
    "comuna": "Frutillar"
  },
  {
    "nombre_local": "UNIMARC ALERCE PTO MONTT",
    "direccion_centro": "Gabriela Mistral S/N",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "UNIMARC CALBUCO ERRAZURIZ",
    "direccion_centro": "Fedrico Errázuriz 211",
    "region": "Región de Los Lagos",
    "comuna": "Calbuco"
  },
  {
    "nombre_local": "UNIMARC LLANQUIHUE BAQUEDANO",
    "direccion_centro": "Baquedano # 612",
    "region": "Región de Los Lagos",
    "comuna": "Llanquihue"
  },
  {
    "nombre_local": "UNIMARC CASTRO O'HIGGINS",
    "direccion_centro": "Ohiigins # 711",
    "region": "Región de Los Lagos",
    "comuna": "Castro"
  },
  {
    "nombre_local": "UNIMARC QUELLON GOMEZ GARCIA",
    "direccion_centro": "GOMEZ GARCIA N320",
    "region": "Región de Los Lagos",
    "comuna": "Quellon"
  },
  {
    "nombre_local": "UNIMARC CARRERA AYSEN",
    "direccion_centro": "Carrera # 1500",
    "region": "Región Aysén del General Carlos Ibáñez del Campo",
    "comuna": "Aysén"
  },
  {
    "nombre_local": "UNIMARC COYHAIQUE LAUTARO",
    "direccion_centro": "Lautaro # 331",
    "region": "Región Aysén del General Carlos Ibáñez del Campo",
    "comuna": "Coyhaique"
  },
  {
    "nombre_local": "UNIMARC ALLENDE AUSTRAL PTA ARENAS",
    "direccion_centro": "Av. Salvador Allende # 0399",
    "region": "Región de Magallanes y de la Antártica Chilena",
    "comuna": "Punta Arenas"
  },
  {
    "nombre_local": "UNIMARC ESPAÑA AUSATRAL PTA.ARENAS",
    "direccion_centro": "Av España # 01375",
    "region": "Región de Magallanes y de la Antártica Chilena",
    "comuna": "Punta Arenas"
  },
  {
    "nombre_local": "UNIMARC ZENTENO AUSTRAL PTA.ARENAS",
    "direccion_centro": "Capitan Guillermo # 05",
    "region": "Región de Magallanes y de la Antártica Chilena",
    "comuna": "Punta Arenas"
  },
  {
    "nombre_local": "UNIMARC PUERTO NATALES BULNES",
    "direccion_centro": "Bulnes # 742",
    "region": "Región de Magallanes y de la Antártica Chilena",
    "comuna": "Natales"
  },
  {
    "nombre_local": "UNIMARC AGUIRRE CERDA PUNTA ARENAS",
    "direccion_centro": "Av. Pedro Aguirre Cerda # 0413",
    "region": "Región de Magallanes y de la Antártica Chilena",
    "comuna": "Punta Arenas"
  },
  {
    "nombre_local": "UNIMARC BORIES AUSTRAL PTA ARENAS",
    "direccion_centro": "Bories # 647",
    "region": "Región de Magallanes y de la Antártica Chilena",
    "comuna": "Punta Arenas"
  },
  {
    "nombre_local": "UNIMARC LAUTARO NAVARRO PTA ARENAS",
    "direccion_centro": "Lautaro Navarro 1293",
    "region": "Región de Magallanes y de la Antártica Chilena",
    "comuna": "Punta Arenas"
  },
  {
    "nombre_local": "MFC LOGISTICA LOS TRAPENSES",
    "direccion_centro": "Jose Alcalde Delano # 10497",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Lo Barnechea"
  },
  {
    "nombre_local": "UNIMARC 2 TRANSVERSAL MAIPU",
    "direccion_centro": "Segunda Transversal # 4090",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipú"
  },
  {
    "nombre_local": "UNIMARC BALMACEDA BUIN",
    "direccion_centro": "Jose Manuel Balmaceda 280",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Buin"
  },
  {
    "nombre_local": "UNIMARC CIUDAD LOS VALLES PUDAHUEL",
    "direccion_centro": "Avenida El Canal # 19591",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Pudahuel"
  },
  {
    "nombre_local": "UNIMARC CURACAVI AMB. O'HIGGINS",
    "direccion_centro": "Av. Ohiggins # 1920",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Curacaví"
  },
  {
    "nombre_local": "UNIMARC EL ABRAZO MAIPU",
    "direccion_centro": "Jorge Guerra # 16190",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipú"
  },
  {
    "nombre_local": "UNIMARC ISLA DE MAIPO SANTELICES",
    "direccion_centro": "Santelices 641",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Isla De Maipo"
  },
  {
    "nombre_local": "UNIMARC LAS CONDES LO BARNECHEA",
    "direccion_centro": "Av. Las Condes # 14791",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Lo Barnechea"
  },
  {
    "nombre_local": "UNIMARC LAS TRANQUERAS VITACURA",
    "direccion_centro": "Av Vitacura # 8400",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Vitacura"
  },
  {
    "nombre_local": "UNIMARC MACUL",
    "direccion_centro": "Av Macul 3578",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Macul"
  },
  {
    "nombre_local": "UNIMARC MAIPO BUIN",
    "direccion_centro": "Camino Buin Maipo 3147",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Buin"
  },
  {
    "nombre_local": "UNIMARC PIRQUE SUBECASEAUX",
    "direccion_centro": "Avenida Ramón Subercaseaux 230",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Pirque"
  },
  {
    "nombre_local": "UNIMARC RECOLETA AVDA. PERU",
    "direccion_centro": "Av. Peru 735, Local 12",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Recoleta"
  },
  {
    "nombre_local": "UNIMARC RENCA BALMACEDA",
    "direccion_centro": "Avenida José Manuel Balmaceda 4569",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Renca"
  },
  {
    "nombre_local": "UNIMARC GRAN AVENIDA SAN MIGUEL",
    "direccion_centro": "Avenida Jose Miguel Carrera # 5485",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Miguel"
  },
  {
    "nombre_local": "UNIMARC ESCUELA MILITAR LAS CONDES",
    "direccion_centro": "Av. Apoquindo # 4335",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Las Condes"
  },
  {
    "nombre_local": "UNIMARC VITACURA VESPUCIO",
    "direccion_centro": "Av. Vitacura # 4607",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Vitacura"
  },
  {
    "nombre_local": "UNIMARC ESTADO SANTIAGO",
    "direccion_centro": "Estado # 85",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "UNIMARC MORANDE SANTIAGO",
    "direccion_centro": "Compañía # 1214",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "UNIMARC MANUEL MONTT PROVIDENCIA",
    "direccion_centro": "Av. Manuel Montt # 1097",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Providencia"
  },
  {
    "nombre_local": "UNIMARC HUECHURABA FONTOVA",
    "direccion_centro": "Av. Pedro Fontova # 7626",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Huechuraba"
  },
  {
    "nombre_local": "UNIMARC CONCHA Y TORO PUENTE ALTO",
    "direccion_centro": "Av.Concha Y Toro N°3193",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Puente Alto"
  },
  {
    "nombre_local": "UNIMARC DORSAL CONCHALI",
    "direccion_centro": "Av. Guanaco # 3100",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Conchalí"
  },
  {
    "nombre_local": "UNIMARC PEÑAFLOR MIRAFLORES",
    "direccion_centro": "MIRAFLORES # 1185",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Peñaflor"
  },
  {
    "nombre_local": "UNIMARC GRECIA ÑUÑOA",
    "direccion_centro": "Av. Grecia # 320",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Ñuñoa"
  },
  {
    "nombre_local": "UNIMARC ROJAS MAGALLANES LA FLORID",
    "direccion_centro": "Rojas Magallanes # 3638",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Florida"
  },
  {
    "nombre_local": "UNIMARC CONSISTOTIAL PEÑALOLEN",
    "direccion_centro": "Av.Consistorial # 2701",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Peñalolén"
  },
  {
    "nombre_local": "UNIMARC LOS MILITARES LAS CONDES",
    "direccion_centro": "Manquehue # 457",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Las Condes"
  },
  {
    "nombre_local": "UNIMARC MANQUEHUE LAS CONDES",
    "direccion_centro": "Av. Manquehue # 1700",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Las Condes"
  },
  {
    "nombre_local": "UNIMARC PRINCIPE DE GALES LA REINA",
    "direccion_centro": "Principe De Gales # 7271",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Reina"
  },
  {
    "nombre_local": "UNIMARC TIL TIL ARTURO PRAT",
    "direccion_centro": "Arturo Prat # 295",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Til Til"
  },
  {
    "nombre_local": "UNIMARC IRARRAZAVAL ÑUÑOA",
    "direccion_centro": "Av. Irarrazaval # 4354",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Ñuñoa"
  },
  {
    "nombre_local": "UNIMARC VICUÑA LA FLORIDA",
    "direccion_centro": "Vicuña mackenna 9090",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Florida"
  },
  {
    "nombre_local": "UNIMARC TALAGANTE O'HIGGINS",
    "direccion_centro": "Ohiigins Lote 1 #2259",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Talagante"
  },
  {
    "nombre_local": "UNIMARC RENCA BRASIL",
    "direccion_centro": "Av Brasil # 7085",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Renca"
  },
  {
    "nombre_local": "UNIMARC JUAN ANT.RIOS SALOMON SACK",
    "direccion_centro": "Salomon Sack # 351",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Independencia"
  },
  {
    "nombre_local": "UNIMARC BATUCO LAMPA",
    "direccion_centro": "Av. Francia # 640",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Lampa"
  },
  {
    "nombre_local": "UNIMARC ALTO JAHUEL BUIN",
    "direccion_centro": "Miraflores 242 Alto Jahuel",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Buin"
  },
  {
    "nombre_local": "UNIMARC SANTA MARIA VITACURA",
    "direccion_centro": "Av. Santa Maria # 6940",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Vitacura"
  },
  {
    "nombre_local": "UNIMARC DIEGO PORTALES SANTIAGO",
    "direccion_centro": "Av Portugal # 56",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "UNIMARC MAIPU CAMINO MELIPILLA",
    "direccion_centro": "Camino Melipilla # 16860",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipú"
  },
  {
    "nombre_local": "UNIMARC IGNACIO CARRERA PINT ÑUÑOA",
    "direccion_centro": "Av Capitan Ignacio Carrera # 3857",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Ñuñoa"
  },
  {
    "nombre_local": "UNIMARC CAMINO NOS SAN BERNARDO",
    "direccion_centro": "Camino Nos A Los Morros N° 565",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Bernardo"
  },
  {
    "nombre_local": "UNIMARC SILVA CARVALLO MAIPU",
    "direccion_centro": "Avd. Silva Carvallo # 1414",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipú"
  },
  {
    "nombre_local": "UNIMARC VICENTE VALDES LA FLORIDA",
    "direccion_centro": "Vicuña Mackena # 7802",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Florida"
  },
  {
    "nombre_local": "UNIMARC LINDEROS BUIN",
    "direccion_centro": "Longitudinal Sur Parc. 11 4251 Linderos",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Buin"
  },
  {
    "nombre_local": "UNIMARC LOS LEONES ÑUÑOA",
    "direccion_centro": "Gral. Jose Artigas # 3250",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Ñuñoa"
  },
  {
    "nombre_local": "UNIMARC LAS VIZCACHAS PUENTE ALTO",
    "direccion_centro": "Av. Camino San José de Maipo, n° domiciliario 06355, local comercial C1",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Puente Alto"
  },
  {
    "nombre_local": "UNIMARC VILLA OLIMPICA ÑUÑOA",
    "direccion_centro": "Obispo Orrego # 1250",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Ñuñoa"
  },
  {
    "nombre_local": "UNIMARC LOS TRAPENSES LO BARNECHEA",
    "direccion_centro": "Jose Alcalde Delano # 10497",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Lo Barnechea"
  },
  {
    "nombre_local": "UNIMARC LARAPINTA LAMPA",
    "direccion_centro": "Av. Los Halcones # 2180",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Lampa"
  },
  {
    "nombre_local": "UNIMARC PUDAHUEL SAN PABLO",
    "direccion_centro": "Av. San Pablo # 8315",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Pudahuel"
  },
  {
    "nombre_local": "UNIMARC MIRADOR LA FLORIDA",
    "direccion_centro": "Avda Vicuña Mackenna # 6331",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Florida"
  },
  {
    "nombre_local": "UNIMARC SAN JOAQUIN STA. ROSA",
    "direccion_centro": "Santa Rosa # 5320",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Joaquín"
  },
  {
    "nombre_local": "UNIMARC CARRASCAL QUINTA NORMAL",
    "direccion_centro": "Gonzalo Bulnes # 2407",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Quinta Normal"
  },
  {
    "nombre_local": "UNIMARC TRONCAL SAN FCO. PTE. ALTO",
    "direccion_centro": "Av. Las Nieves Oriente N° 02251 (Esquina Av. Troncal San Francisco)",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Puente Alto"
  },
  {
    "nombre_local": "UNIMARC EL BOSQUE J.M. CARRERA",
    "direccion_centro": "Av José Miguel Carrera 13.125",
    "region": "Región Metropolitana de Santiago",
    "comuna": "El Bosque"
  },
  {
    "nombre_local": "UNIMARC PAJARITOS ESTACION CENTRAL",
    "direccion_centro": "Av Gladys Marin 6950",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Estación Central"
  },
  {
    "nombre_local": "UNIMARC MAIPU 4 PONIENTE",
    "direccion_centro": "4 Poniente # 1197",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipú"
  },
  {
    "nombre_local": "UNIMARC METRO LO OVALLE LA CISTERN",
    "direccion_centro": "Gran Avenida # 6555",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Cisterna"
  },
  {
    "nombre_local": "UNIMARC FRANSIC BILBAO PROVIDENCIA",
    "direccion_centro": "Av Francisco Bilbao # 2050",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Providencia"
  },
  {
    "nombre_local": "UNIMARC INDEPENDENCIA HIPODROMO",
    "direccion_centro": "Independencia 2127",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Independencia"
  },
  {
    "nombre_local": "UNIMARC MAIPU EL ROSAL",
    "direccion_centro": "Avda. El Rosal # 6361",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipú"
  },
  {
    "nombre_local": "UNIMARC PANGUIPULLI P. DE VALDIVIA",
    "direccion_centro": "Pedro De Valdivia N° 115",
    "region": "Región de Los Ríos",
    "comuna": "Panguipulli"
  },
  {
    "nombre_local": "UNIMARC RIO BUENO PEDRO LAGOS",
    "direccion_centro": "Pedro Lagos # 593",
    "region": "Región de Los Ríos",
    "comuna": "Río Bueno"
  },
  {
    "nombre_local": "UNIMARC ARAUCO VALDIVIA",
    "direccion_centro": "Arauco N° 697",
    "region": "Región de Los Ríos",
    "comuna": "Valdivia"
  },
  {
    "nombre_local": "UNIMARC LA UNION SERRANO",
    "direccion_centro": "Serrano # 617",
    "region": "Región de Los Ríos",
    "comuna": "La Unión"
  },
  {
    "nombre_local": "UNIMARC LOS LAGOS BALMACEDA",
    "direccion_centro": "Balmaceda Norte N° 79",
    "region": "Región de Los Ríos",
    "comuna": "Los Lagos"
  },
  {
    "nombre_local": "UNIMARC LAS ANIMAS VALDIVIA",
    "direccion_centro": "Bombero Classing N° 204",
    "region": "Región de Los Ríos",
    "comuna": "Valdivia"
  },
  {
    "nombre_local": "UNIMARC VALDIVIA FRANCIA",
    "direccion_centro": "Avda Francia # 2651",
    "region": "Región de Los Ríos",
    "comuna": "Valdivia"
  },
  {
    "nombre_local": "UNIMARC YUNGAY VALDIVIA",
    "direccion_centro": "Yungay # 420",
    "region": "Región de Los Ríos",
    "comuna": "Valdivia"
  },
  {
    "nombre_local": "UNIMARC LOS LAGOS QUINCHILCA",
    "direccion_centro": "Quinchilca N° 334",
    "region": "Región de Los Ríos",
    "comuna": "Los Lagos"
  },
  {
    "nombre_local": "UNIMARC PAILLACO ARTURO PRAT",
    "direccion_centro": "Arturo Prat N° 688",
    "region": "Región de Los Ríos",
    "comuna": "Paillaco"
  },
  {
    "nombre_local": "UNIMARC ROTONDA ARICA",
    "direccion_centro": "18 De Septiembre # 2501",
    "region": "Región de Arica y Parinacota",
    "comuna": "Arica"
  },
  {
    "nombre_local": "UNIMARC SANTA MARIA ARICA",
    "direccion_centro": "Santa Maria # 2465",
    "region": "Región de Arica y Parinacota",
    "comuna": "Arica"
  },
  {
    "nombre_local": "UNIMARC CHILLAN PRAT",
    "direccion_centro": "Av 5 De Abril 864",
    "region": "Región de Ñuble",
    "comuna": "Chillán"
  },
  {
    "nombre_local": "UNIMARC PALACIOS BULNES",
    "direccion_centro": "Carlos Palacios #151",
    "region": "Región de Ñuble",
    "comuna": "Bulnes"
  },
  {
    "nombre_local": "UNIMARC CHILLAN VIEJO O'HIGGINS",
    "direccion_centro": "Av. Bernardo O'Higgins 2305",
    "region": "Región de Ñuble",
    "comuna": "Chillán Viejo"
  },
  {
    "nombre_local": "UNIMARC SAN CARLOS IGNACIO SERRANO",
    "direccion_centro": "Ignacio Serrano 500",
    "region": "Región de Ñuble",
    "comuna": "San Carlos"
  },
  {
    "nombre_local": "UNIMARC CHILLAN COLLIN",
    "direccion_centro": "Collín 866",
    "region": "Región de Ñuble",
    "comuna": "Chillán"
  },
  {
    "nombre_local": "UNIMARC CHILLAN 5 DE ABRIL",
    "direccion_centro": "5 De abril 0754",
    "region": "Región de Ñuble",
    "comuna": "Chillán"
  },
  {
    "nombre_local": "UNIMARC COIHUECO BALMACEDA",
    "direccion_centro": "Balmaceda 546",
    "region": "Región de Ñuble",
    "comuna": "Coihueco"
  },
  {
    "nombre_local": "UNIMARC COELEMU CASTELLON",
    "direccion_centro": "Castellón 597",
    "region": "Región de Ñuble",
    "comuna": "Coelemu"
  },
  {
    "nombre_local": "UNIMARC QUILLON CAYUMANQUI",
    "direccion_centro": "Cayumanqui #495",
    "region": "Región de Ñuble",
    "comuna": "Quillón"
  },
  {
    "nombre_local": "UNIMARC EL CARMEN ESMERALDA",
    "direccion_centro": "Esmeralda 550",
    "region": "Región de Ñuble",
    "comuna": "El Carmen"
  },
  {
    "nombre_local": "UNIMARC YUNGAY ESMERALDA",
    "direccion_centro": "Esmeralda 211",
    "region": "Región de Ñuble",
    "comuna": "Yungay"
  }
]

# Centros para SUPER 10 S.A.
CENTROS_SUPER10 = [
  {
    "nombre_local": "M10 OVALLE I",
    "direccion_centro": "Benavente 427",
    "region": "Región de Coquimbo",
    "comuna": "Ovalle"
  },
  {
    "nombre_local": "M10 OVALLE II",
    "direccion_centro": "Victoria 435",
    "region": "Región de Coquimbo",
    "comuna": "Ovalle"
  },
  {
    "nombre_local": "M10 SAN ANTONIO",
    "direccion_centro": "Pedro Montt 148",
    "region": "Región de Valparaíso",
    "comuna": "San Antonio"
  },
  {
    "nombre_local": "S10 LIMACHE",
    "direccion_centro": "ARTUTO PRAT 200",
    "region": "Región de Valparaíso",
    "comuna": "Limache"
  },
  {
    "nombre_local": "M10 SAN FELIPE",
    "direccion_centro": "Santo Domingo 111",
    "region": "Región de Valparaíso",
    "comuna": "San Felipe"
  },
  {
    "nombre_local": "M10 LA CALERA",
    "direccion_centro": "Carrera 949",
    "region": "Región de Valparaíso",
    "comuna": "La Calera"
  },
  {
    "nombre_local": "M10 VILLA ALEMANA",
    "direccion_centro": "Av. Valparaiso 517",
    "region": "Región de Valparaíso",
    "comuna": "Villa Alemana"
  },
  {
    "nombre_local": "M10 EL BELLOTO",
    "direccion_centro": "Baden Powell 36",
    "region": "Región de Valparaíso",
    "comuna": "Quilpué"
  },
  {
    "nombre_local": "M10 VALPARAISO",
    "direccion_centro": "Pedro Montt 2585",
    "region": "Región de Valparaíso",
    "comuna": "Valparaíso"
  },
  {
    "nombre_local": "M10 SANTA CRUZ",
    "direccion_centro": "Ramon Sanfurgo 66",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Santa Cruz"
  },
  {
    "nombre_local": "M10 RANCAGUA II",
    "direccion_centro": "Avenida Brasil N° 1016",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Rancagua"
  },
  {
    "nombre_local": "M10 RENGO",
    "direccion_centro": "Arturo Prat 607",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Rengo"
  },
  {
    "nombre_local": "M10 SAN FERNANDO",
    "direccion_centro": "Chillán 745",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "San Fernando"
  },
  {
    "nombre_local": "M10 SAN VICENTE",
    "direccion_centro": "Avda España Esq Genaro Lisboa",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "San Vicente"
  },
  {
    "nombre_local": "S10 RANCAGUA III",
    "direccion_centro": "Avenida Brasil N° 1064",
    "region": "Región del Libertador General Bernardo O'Higgins",
    "comuna": "Rancagua"
  },
  {
    "nombre_local": "M10 CURICO",
    "direccion_centro": "Camilo Henríquez 898",
    "region": "Región del Maule",
    "comuna": "Curicó"
  },
  {
    "nombre_local": "M10 LINARES",
    "direccion_centro": "Av. Brasil 646-648",
    "region": "Región del Maule",
    "comuna": "Linares"
  },
  {
    "nombre_local": "M10 CAÑETE",
    "direccion_centro": "Saavedra 955",
    "region": "Región del Biobío",
    "comuna": "Cañete"
  },
  {
    "nombre_local": "M10 LOS ANGELES",
    "direccion_centro": "Av. Sor Vicenta 2141",
    "region": "Región del Biobío",
    "comuna": "Los Angeles"
  },
  {
    "nombre_local": "M10 HUALPEN II",
    "direccion_centro": "Nueva Imperial 113",
    "region": "Región del Biobío",
    "comuna": "Hualpén"
  },
  {
    "nombre_local": "M10 CONCEPCION I",
    "direccion_centro": "Carrera 637",
    "region": "Región del Biobío",
    "comuna": "Concepción"
  },
  {
    "nombre_local": "M10 TOME",
    "direccion_centro": "Ignacio Serrano 908",
    "region": "Región del Biobío",
    "comuna": "Tomé"
  },
  {
    "nombre_local": "M10 HUALPEN",
    "direccion_centro": "Colón 7948",
    "region": "Región del Biobío",
    "comuna": "Hualpén"
  },
  {
    "nombre_local": "M10 ANGOL",
    "direccion_centro": "Av. O'Higgins N' 1815",
    "region": "Región de La Araucanía",
    "comuna": "Angol"
  },
  {
    "nombre_local": "M10 TEMUCO IV",
    "direccion_centro": "Avda Francisco Salazar 1650",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "M10 TEMUCO II",
    "direccion_centro": "Av. Pedro De Valdivia 2285",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "M10 TEMUCO V",
    "direccion_centro": "Miraflores 1230",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "M10 TEMUCO III",
    "direccion_centro": "Av. Anibal Pinto 172",
    "region": "Región de La Araucanía",
    "comuna": "Temuco"
  },
  {
    "nombre_local": "M10 PUERTO MONTT",
    "direccion_centro": "Presidente Ibañez 316",
    "region": "Región de Los Lagos",
    "comuna": "Puerto Montt"
  },
  {
    "nombre_local": "M10 SAN MARTIN",
    "direccion_centro": "Avda. San Martin 460",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Bernardo"
  },
  {
    "nombre_local": "S10 Camilo Henriquez",
    "direccion_centro": "Avenida Camilo Henriquez 5239",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Puente Alto"
  },
  {
    "nombre_local": "S10 EL PEÑON",
    "direccion_centro": "AV. MEXICO 1915",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Puente Alto"
  },
  {
    "nombre_local": "S10 LAMPA",
    "direccion_centro": "Arturo Prat 681",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Lampa"
  },
  {
    "nombre_local": "S10 MAIPU IV",
    "direccion_centro": "AV. Alfredo Silva Carvallo 1401",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipu"
  },
  {
    "nombre_local": "S10 Peñaflor",
    "direccion_centro": "Avenida 21 De Mayo 4215",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Peñaflor"
  },
  {
    "nombre_local": "S10 Rojas Magallanes",
    "direccion_centro": "Avenida Rojas Magallanes 1856",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Florida"
  },
  {
    "nombre_local": "M10 CERRILLOS",
    "direccion_centro": "Americo Vespucio 1601",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Cerrillos"
  },
  {
    "nombre_local": "M10 21 MAYO",
    "direccion_centro": "21 De mayo 0819",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "M10 LA CISTERNA",
    "direccion_centro": "Gran Avenida 9150",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Cisterna"
  },
  {
    "nombre_local": "M10 VICUÑA MACKENNA",
    "direccion_centro": "Avenida Serafin Zamora 127",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Florida"
  },
  {
    "nombre_local": "M10 MARATHON",
    "direccion_centro": "Av.Marathon N°3123",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "M10 LO PRADO",
    "direccion_centro": "Av. San Pablo 6702",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "M10 SAN BERNARDO I",
    "direccion_centro": "Av. Portales 2448",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Bernardo"
  },
  {
    "nombre_local": "M10 RECOLETA",
    "direccion_centro": "Av.El Salto N°2506",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "S10 GRAN AVENIDA",
    "direccion_centro": "Gran Avenida 6060",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Miguel"
  },
  {
    "nombre_local": "M10 MAIPU III",
    "direccion_centro": "Camino Melipilla 18300",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipú"
  },
  {
    "nombre_local": "M10 BUIN",
    "direccion_centro": "Manuel Rodríguez 312 Buin",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Buin"
  },
  {
    "nombre_local": "M10 SAN DIEGO",
    "direccion_centro": "San Diego 2115",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "S10 GABRIELA",
    "direccion_centro": "Avenida Gabriela Oriente 0651",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Puente Alto"
  },
  {
    "nombre_local": "M10 PAJARITOS",
    "direccion_centro": "Av.Gladys Marin 6480",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Estación Central"
  },
  {
    "nombre_local": "S10 LA TRAVESÍA",
    "direccion_centro": "Avenida Diagonal Teniente Cruz 530",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Pudahuel"
  },
  {
    "nombre_local": "M10 COLINA",
    "direccion_centro": "Carretera General San Martin 381",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Colina"
  },
  {
    "nombre_local": "M10 PUENTE ALTO II",
    "direccion_centro": "Avenida Concha Y Toro 4115",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Puente Alto"
  },
  {
    "nombre_local": "M10 SAN JOAQUIN",
    "direccion_centro": "Llico 456",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Joaquín"
  },
  {
    "nombre_local": "M10 LA FLORIDA",
    "direccion_centro": "Avenida San Jose De La Estrella 1392",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Florida"
  },
  {
    "nombre_local": "M10 MAIPU II",
    "direccion_centro": "2 Norte 1373",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Maipú"
  },
  {
    "nombre_local": "S10 PORTALES",
    "direccion_centro": "Avda Portales Oriente 1701",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Bernardo"
  },
  {
    "nombre_local": "M10 SAN PABLO II",
    "direccion_centro": "Av. San Pablo N° 8537",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "M10 SAN LUIS",
    "direccion_centro": "Avda San Luis N° 5171",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Santiago"
  },
  {
    "nombre_local": "S10 RENCA",
    "direccion_centro": "dirección Miraflores 8045, RENCA",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Renca"
  },
  {
    "nombre_local": "M10 SANTA ROSA",
    "direccion_centro": "Avda Santa Rosa 7576",
    "region": "Región Metropolitana de Santiago",
    "comuna": "La Granja"
  },
  {
    "nombre_local": "M10 SAN BERNARDO II",
    "direccion_centro": "Av. Bulnes 550",
    "region": "Región Metropolitana de Santiago",
    "comuna": "San Bernardo"
  },
  {
    "nombre_local": "S10 QUILICURA",
    "direccion_centro": "José Francisco Vergara 159",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Quilicura"
  },
  {
    "nombre_local": "M10 PAJARITOS II",
    "direccion_centro": "Av.Gladys Marin 6664",
    "region": "Región Metropolitana de Santiago",
    "comuna": "Estación Central"
  },
  {
    "nombre_local": "M10 LA UNION",
    "direccion_centro": "Esmeralda 751",
    "region": "Región de Los Ríos",
    "comuna": "La Unión"
  },
  {
    "nombre_local": "M10 VALDIVIA",
    "direccion_centro": "Av.Ramon Picarte 2593",
    "region": "Región de Los Ríos",
    "comuna": "Valdivia"
  },
  {
    "nombre_local": "M10 CHILLAN AP",
    "direccion_centro": "Arturo Prat 879 - Local 76, Paseo La Merced",
    "region": "Región de Ñuble",
    "comuna": "Chillán"
  },
  {
    "nombre_local": "M10 CHILLAN I RIQUELME",
    "direccion_centro": "Isabel Riquelme 959",
    "region": "Región de Ñuble",
    "comuna": "Chillán"
  }
]

# Filas con etiqueta de empresa no mapeada (diagnóstico)
UNMAPPED_DEBUG = []

@transaction.atomic
def run():
    # LIMPIEZA (orden por FKs)
    AccidenteJsonData.objects.all().delete()
    Prescripciones.objects.all().delete()
    PreguntasGuia.objects.all().delete()
    Informes.objects.all().delete()
    Hechos.objects.all().delete()
    Documentos.objects.all().delete()
    Declaraciones.objects.all().delete()
    ArbolCausas.objects.all().delete()
    Accidentes.objects.all().delete()
    CentrosTrabajo.objects.all().delete()
    Trabajadores.objects.all().delete()
    Empresas.objects.all().delete()
    Holdings.objects.all().delete()
    # OJO: NO borramos usuarios

    # HOLDING + EMPRESAS SMU
    holding = Holdings.objects.create(nombre="SMU")

    rendic = Empresas.objects.create(
        holding=holding,
        empresa_sel="RENDIC HERMANOS S.A.",
        rut_empresa="81.537.600-5",
        actividad="Supermercados",
        direccion_empresa="Cerro el plomo 5680",
        telefono="",
        representante_legal="",
        region="Metropolitana",
        comuna="Las condes",
    )

    super10 = Empresas.objects.create(
        holding=holding,
        empresa_sel="SUPER 10 S.A.",
        rut_empresa="76.012.833-3",
        actividad="Supermercados",
        direccion_empresa="Cerro el plomo 5680",
        telefono="",
        representante_legal="",
        region="Metropolitana",
        comuna="Las condes",
    )

    created, updated = 0, 0

    # Insertar/actualizar centros de RENDIC
    for row in CENTROS_RENDIC:
        obj, was_created = CentrosTrabajo.objects.update_or_create(
            empresa=rendic,
            nombre_local=row["nombre_local"],
            defaults={
                "direccion_centro": row["direccion_centro"],
                "region": row["region"],
                "comuna": row["comuna"],
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1

    # Insertar/actualizar centros de SUPER 10
    for row in CENTROS_SUPER10:
        obj, was_created = CentrosTrabajo.objects.update_or_create(
            empresa=super10,
            nombre_local=row["nombre_local"],
            defaults={
                "direccion_centro": row["direccion_centro"],
                "region": row["region"],
                "comuna": row["comuna"],
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1

    print(f"Holding creado: {{holding.nombre}}")
    print(f"Empresas creadas: {{rendic.empresa_sel}} (id={{rendic.pk}}), {{super10.empresa_sel}} (id={{super10.pk}})")
    print(f"Centros creados: {{created}}, actualizados: {{updated}}")
    if UNMAPPED_DEBUG:
        print(f"Aviso: hay {{len(UNMAPPED_DEBUG)}} filas con etiqueta de empresa no mapeada.")

if __name__ == "__main__":
    run()
