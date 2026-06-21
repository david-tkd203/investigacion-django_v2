# cargar_datos_completo.py

from django.db import transaction
from django.contrib.auth import get_user_model
from accidentes.models import (
    Holdings, Empresas, CentrosTrabajo, Trabajadores,
    Accidentes, ArbolCausas, Declaraciones, Documentos,
    Hechos, Informes, PreguntasGuia, Prescripciones, AccidenteJsonData
)
from datetime import time, date
import uuid

User = get_user_model()

@transaction.atomic
def run():
    # NO borramos holdings/empresas existentes (vienen de scripts embebidos)
    # Solo borramos datos de casos anteriores para poder re-ejecutar
    AccidenteJsonData.objects.all().delete()
    Prescripciones.objects.all().delete()
    PreguntasGuia.objects.all().delete()
    Informes.objects.all().delete()
    Hechos.objects.all().delete()
    Documentos.objects.all().delete()
    Declaraciones.objects.all().delete()
    ArbolCausas.objects.all().delete()
    Accidentes.objects.all().delete()
    # OJO: NO tocamos accounts.User para no borrar el superusuario

    # Usar empresas existentes (de los scripts embebidos) o crear demo si no hay
    qs = Empresas.objects.all()
    if qs.count() >= 2:
        empresa1 = qs[0]
        empresa2 = qs[1]
    elif qs.count() == 1:
        empresa1 = qs[0]
        # Crear segunda empresa demo
        h, _ = Holdings.objects.get_or_create(nombre="Demo Holding")
        empresa2 = Empresas.objects.create(
            holding=h, empresa_sel="Constructora Demo Ltda.",
            rut_empresa="98765432-1", actividad="Construcción",
            direccion_empresa="Alameda 456", telefono="+56987654321",
            representante_legal="Ana Rojas",
            region="Valparaíso", comuna="Viña del Mar"
        )
    else:
        # Todo desde cero
        h, _ = Holdings.objects.get_or_create(nombre="Grupo Demo")
        empresa1 = Empresas.objects.create(
            holding=h, empresa_sel="Maestranza Demo S.A.",
            rut_empresa="12345678-9", actividad="Metalúrgica",
            direccion_empresa="Av. Siempre Viva 123", telefono="+56912345678",
            representante_legal="Juan Pérez", region="Metropolitana", comuna="Santiago"
        )
        empresa2 = Empresas.objects.create(
            holding=h, empresa_sel="Constructora Demo Ltda.",
            rut_empresa="98765432-1", actividad="Construcción",
            direccion_empresa="Alameda 456", telefono="+56987654321",
            representante_legal="Ana Rojas",
            region="Valparaíso", comuna="Viña del Mar"
        )

    # Asegurar centros de trabajo
    centros_e1 = list(CentrosTrabajo.objects.filter(empresa=empresa1))
    if not centros_e1:
        centros_e1 = [
            CentrosTrabajo.objects.create(empresa=empresa1, nombre_local="Planta Santiago",
                direccion_centro="Camino Industrial 100", region="Metropolitana", comuna="Santiago"),
            CentrosTrabajo.objects.create(empresa=empresa1, nombre_local="Planta Sur",
                direccion_centro="Ruta 5 Sur km 10", region="Metropolitana", comuna="San Bernardo"),
        ]
    centros_e2 = list(CentrosTrabajo.objects.filter(empresa=empresa2))
    if not centros_e2:
        centros_e2 = [
            CentrosTrabajo.objects.create(empresa=empresa2, nombre_local="Obra Reñaca",
                direccion_centro="Reñaca Norte s/n", region="Valparaíso", comuna="Viña del Mar"),
        ]

    # Usar usuario existente (admin)
    usuario = User.objects.filter(is_superuser=True).first()
    if not usuario:
        usuario = User.objects.first()
    if not usuario:
        print("  AVISO: No hay usuarios, no se crean casos")
        return

    # Crear trabajador
    holding = empresa1.holding or Holdings.objects.first()
    trabajador = Trabajadores.objects.create(
        empresa=empresa1,
        nombre_trabajador="Luis Soto",
        rut_trabajador="22222222-2",
        fecha_nacimiento=date(1990, 5, 20),
        nacionalidad="Chilena",
        estado_civil="Soltero/a",
        domicilio="Calle Falsa 456",
        cargo_trabajador="Operario",
        contrato="Indefinido"
    )

    centro = centros_e1[0]

    base_code = "CASO-001"
    code = base_code
    i = 1
    while Accidentes.objects.filter(codigo_accidente=code).exists():
        i += 1
        code = f"{base_code}-{i}"

    accidente = Accidentes.objects.create(
        holding=holding, empresa=empresa1, centro=centro,
        trabajador=trabajador, usuario_asignado=usuario, creado_por=usuario,
        fecha_accidente=date(2024, 6, 10), hora_accidente=time(14, 30),
        lugar_accidente="Zona de corte", tipo_accidente="Golpe por",
        naturaleza_lesion="Corte profundo", parte_afectada="Mano derecha",
        tarea="Cortar planchas", operacion="Laminado",
        danos_personas="SI", danos_propiedad="NO", perdidas_proceso="SI",
        contexto="Alta demanda de producción",
        circunstancias="Uso de máquina sin protección",
        codigo_accidente=code
    )

    Declaraciones.objects.create(
        accidente=accidente, tipo_decl="accidentado",
        nombre="Luis Soto", rut="22222222-2", cargo="Operario",
        texto="Estaba utilizando la máquina sin protector cuando ocurrió el corte."
    )

    Hechos.objects.create(
        accidente=accidente, secuencia=1,
        descripcion="El trabajador manipulaba una máquina sin protección."
    )

    Informes.objects.create(
        accidente=accidente, version=1, is_current=True,
        codigo="INF-2024-001", fecha_informe=date(2024, 6, 15),
        investigador="María González"
    )

    Prescripciones.objects.create(
        accidente=accidente, tipo="Seguridad", prioridad="Alta",
        plazo=date(2024, 7, 1), responsable="Jefe de turno",
        descripcion="Instalar protectores en todas las máquinas."
    )

    ArbolCausas.objects.create(
        accidente=accidente, version=1, is_current=True,
        arbol_json_5q='{"0.0.0.0.0.0.0.0.0": "Corte superficial en mano"}',
        arbol_json_dot='digraph { node_0 [label="Corte"]; }'
    )

    # Segundo caso vacío
    trabajador_vacio = Trabajadores.objects.create(
        empresa=empresa2, nombre_trabajador="", rut_trabajador="",
        fecha_nacimiento=None, nacionalidad="", estado_civil="",
        domicilio="", cargo_trabajador="", contrato=""
    )
    centro_vacio = centros_e2[0] if centros_e2 else None

    code2 = "CASO-002"
    j = 1
    while Accidentes.objects.filter(codigo_accidente=code2).exists():
        j += 1
        code2 = f"CASO-002-{j}"

    Accidentes.objects.create(
        holding=holding, empresa=empresa2, centro=centro_vacio,
        trabajador=trabajador_vacio, usuario_asignado=usuario, creado_por=usuario,
        codigo_accidente=code2
    )

    # Asignar admin a la primera empresa si no tiene
    if usuario.empresa_id is None:
        usuario.empresa = empresa1
        usuario.holding = holding
        usuario.save()

# Si lo ejecutas con `manage.py shell`, llama a run():
if __name__ == "__main__":
    run()
