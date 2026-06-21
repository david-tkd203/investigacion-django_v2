import os
from datetime import date, time
from django.db.models.signals import pre_save, post_save
from accidentes.models import Holdings, Empresas, CentrosTrabajo, Trabajadores, Usuarios, Accidentes

print("\n[DEMO] Desconectando signals para evitar envio de correos...")
# Desactivar signals temporalmente
pre_save.disconnect(sender=Accidentes)
post_save.disconnect(sender=Accidentes)

# 1. Holding
holding = Holdings.objects.create(nombre="Grupo Prueba")

# 2. Empresa
empresa = Empresas.objects.create(
    holding=holding,
    empresa_sel="Constructora Prueba S.A.",
    rut_empresa="76543210-0",
    actividad="Construcción",
    direccion_empresa="Av. Central 123",
    telefono="987654321",
    representante_legal="Carlos Gómez",
    region="Metropolitana",
    comuna="Santiago"
)

# 3. Centro de trabajo
centro = CentrosTrabajo.objects.create(
    empresa=empresa,
    region="Metropolitana",
    comuna="Providencia",
    nombre_local="Obra Kennedy",
    direccion_centro="Av. Kennedy 321"
)

# 4. Usuario
usuario = Usuarios.objects.create(
    rut="11111111-1",
    nombre="Andrea",
    apepat="Rodríguez",
    apemat="Muñoz",
    email="andrea@demo.cl",
    empresa=empresa,
    pass_field=os.getenv("DEMO_USER_PASSWORD", ""),
    tipo=1,
    Cargo="Consultor"  # coincide con tu modelo (con C mayúscula)
)

# 5. Trabajadores
trabajadores = [
    Trabajadores.objects.create(
        empresa=empresa,
        nombre_trabajador="Juan Pérez",
        rut_trabajador="12345678-9",
        fecha_nacimiento="1990-05-10",
        nacionalidad="Chilena",
        estado_civil="Soltero",
        domicilio="Calle A 123",
        antiguedad_empresa="2 años",
        antiguedad_cargo="6 meses",
        cargo_trabajador="Obrero"
    ),
    Trabajadores.objects.create(
        empresa=empresa,
        nombre_trabajador="María González",
        rut_trabajador="15678910-2",
        fecha_nacimiento="1985-11-20",
        nacionalidad="Chilena",
        estado_civil="Casada",
        domicilio="Calle B 456",
        antiguedad_empresa="3 años",
        antiguedad_cargo="9 meses",
        cargo_trabajador="Capataz"
    ),
    Trabajadores.objects.create(
        empresa=empresa,
        nombre_trabajador="Luis Rojas",
        rut_trabajador="17111222-3",
        fecha_nacimiento="1992-03-15",
        nacionalidad="Chilena",
        estado_civil="Soltero",
        domicilio="Calle C 789",
        antiguedad_empresa="1 año",
        antiguedad_cargo="3 meses",
        cargo_trabajador="Técnico"
    )
]

# 6. Accidentes
accidentes_info = [
    ("IST2024-001", "Caída desde altura", "Pierna", "Sí", "No", "No", "Fractura expuesta"),
    ("IST2024-002", "Golpe con objeto", "Brazo", "No", "Sí", "Sí", "Contusión leve"),
    ("IST2024-003", "Contacto con electricidad", "Mano", "Sí", "Sí", "No", "Quemadura leve")
]

for i, (codigo, tipo, parte, dp, dprop, perd, contexto) in enumerate(accidentes_info):
    Accidentes.objects.create(
        centro=centro,
        trabajador=trabajadores[i],
        usuario=usuario,
        fecha_accidente=date(2024, 7, 1 + i),
        hora_accidente=time(9 + i, 0),
        lugar_accidente=f"Zona de trabajo {i + 1}",
        tipo_accidente=tipo,
        naturaleza_lesion=f"Lesión {i + 1}",
        parte_afectada=parte,
        tarea=f"Tarea {i + 1}",
        operacion=f"Operación {i + 1}",
        cargo_trabajador=trabajadores[i].cargo_trabajador,
        contrato="Indefinido",
        antiguedad_empresa=trabajadores[i].antiguedad_empresa,
        antiguedad_cargo=trabajadores[i].antiguedad_cargo,
        danos_personas=dp,
        danos_propiedad=dprop,
        perdidas_proceso=perd,
        contexto=contexto,
        circunstancias=f"Circunstancias del accidente {i + 1}",
        codigo_accidente=codigo
    )

print("✅ 3 accidentes cargados con éxito.")
