"""
Tests de la app principal — accidentes.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date, time
from .models import (
    Holdings, Empresas, CentrosTrabajo, Trabajadores,
    Accidentes, Declaraciones, Hechos, ArbolCausas,
    PreguntasGuia, Prescripciones, Informes, Documentos
)
from .constants import ROLE_SUPER_ADMIN

User = get_user_model()


# ─── Helpers ──────────────────────────────────────────────

def crear_usuario_admin():
    return User.objects.create_user(
        username="admin",
        rut="11111111-1",
        password="admin123",
        is_superuser=True,
        is_staff=True,
    )

def crear_holding():
    return Holdings.objects.create(nombre="Test Holding")

def crear_empresa(holding=None):
    if not holding:
        holding = crear_holding()
    return Empresas.objects.create(
        holding=holding,
        empresa_sel="Test S.A.",
        rut_empresa="12345678-9",
        actividad="Testing",
        region="Metropolitana",
        comuna="Santiago",
    )

def crear_centro(empresa=None):
    if not empresa:
        empresa = crear_empresa()
    return CentrosTrabajo.objects.create(
        empresa=empresa,
        nombre_local="Test Center",
        region="Metropolitana",
        comuna="Santiago",
        direccion_centro="Calle Falsa 123",
    )

def crear_trabajador(empresa=None):
    if not empresa:
        empresa = crear_empresa()
    return Trabajadores.objects.create(
        empresa=empresa,
        nombre_trabajador="Juan Perez",
        rut_trabajador="22222222-2",
        cargo_trabajador="Operario",
        contrato="Indefinido",
    )


# ─── Model Tests ──────────────────────────────────────────

class HoldingsModelTest(TestCase):
    def test_create_holding(self):
        h = Holdings.objects.create(nombre="Test Holding")
        self.assertEqual(str(h), "Test Holding")

    def test_holding_auto_timestamps(self):
        h = Holdings.objects.create(nombre="Timed")
        self.assertIsNotNone(h.created_at)


class EmpresasModelTest(TestCase):
    def setUp(self):
        self.holding = Holdings.objects.create(nombre="Holding")

    def test_create_empresa(self):
        e = Empresas.objects.create(
            holding=self.holding,
            empresa_sel="Test S.A.",
            rut_empresa="12345678-9",
        )
        self.assertEqual(str(e), "Test S.A.")

    def test_empresa_unique_rut(self):
        Empresas.objects.create(
            holding=self.holding, empresa_sel="A", rut_empresa="unique-1"
        )
        with self.assertRaises(Exception):
            Empresas.objects.create(
                holding=self.holding, empresa_sel="B", rut_empresa="unique-1"
            )


class AccidentesModelTest(TestCase):
    def setUp(self):
        self.user = crear_usuario_admin()
        self.holding = crear_holding()
        self.empresa = crear_empresa(self.holding)
        self.centro = crear_centro(self.empresa)
        self.trabajador = crear_trabajador(self.empresa)

    def test_create_accidente(self):
        acc = Accidentes.objects.create(
            holding=self.holding,
            empresa=self.empresa,
            centro=self.centro,
            trabajador=self.trabajador,
            usuario_asignado=self.user,
            creado_por=self.user,
            fecha_accidente=date(2025, 1, 15),
            hora_accidente=time(10, 30),
            lugar_accidente="Bodega",
            tipo_accidente="Caída",
            naturaleza_lesion="Fractura",
            codigo_accidente="QA-001",
        )
        self.assertEqual(acc.codigo_accidente, "QA-001")
        self.assertIn("QA-001", str(acc))

    def test_accidente_unique_codigo(self):
        Accidentes.objects.create(
            codigo_accidente="UNIQUE-1",
            holding=self.holding,
            empresa=self.empresa,
            trabajador=self.trabajador,
            usuario_asignado=self.user,
            creado_por=self.user,
        )
        with self.assertRaises(Exception):
            Accidentes.objects.create(
                codigo_accidente="UNIQUE-1",
                holding=self.holding,
                empresa=self.empresa,
                trabajador=self.trabajador,
                usuario_asignado=self.user,
                creado_por=self.user,
            )


class ArbolCausasModelTest(TestCase):
    def setUp(self):
        self.user = crear_usuario_admin()
        self.holding = crear_holding()
        self.empresa = crear_empresa(self.holding)
        self.centro = crear_centro(self.empresa)
        self.trabajador = crear_trabajador(self.empresa)
        self.accidente = Accidentes.objects.create(
            codigo_accidente="ARBOL-TEST",
            holding=self.holding,
            empresa=self.empresa,
            centro=self.centro,
            trabajador=self.trabajador,
            usuario_asignado=self.user,
            creado_por=self.user,
        )

    def test_create_arbol(self):
        arbol = ArbolCausas.objects.create(
            accidente=self.accidente,
            version=1,
            is_current=True,
        )
        self.assertTrue(arbol.is_current)

    def test_arbol_json_field(self):
        arbol = ArbolCausas.objects.create(
            accidente=self.accidente,
            version=1,
            is_current=True,
            arbol_json_5q='{"test": "data"}',
        )
        self.assertIn("test", arbol.arbol_json_5q)


class DeclaracionesModelTest(TestCase):
    def setUp(self):
        self.user = crear_usuario_admin()
        self.holding = crear_holding()
        self.empresa = crear_empresa(self.holding)
        self.centro = crear_centro(self.empresa)
        self.trabajador = crear_trabajador(self.empresa)
        self.accidente = Accidentes.objects.create(
            codigo_accidente="DECL-TEST",
            holding=self.holding,
            empresa=self.empresa,
            trabajador=self.trabajador,
            usuario_asignado=self.user,
            creado_por=self.user,
        )

    def test_create_declaracion(self):
        dec = Declaraciones.objects.create(
            accidente=self.accidente,
            tipo_decl="accidentado",
            nombre="Test",
            texto="Relato de prueba",
        )
        self.assertEqual(dec.tipo_decl, "accidentado")


# ─── View Tests ───────────────────────────────────────────

class LoginRequiredViewTests(TestCase):
    def setUp(self):
        self.user = crear_usuario_admin()
        self.user.rol = ROLE_SUPER_ADMIN
        self.user.save()
        self.holding = crear_holding()
        self.empresa = crear_empresa(self.holding)
        self.user.empresa = self.empresa
        self.user.holding = self.holding
        self.user.save()
        self.centro = crear_centro(self.empresa)
        self.trabajador = crear_trabajador(self.empresa)
        self.accidente = Accidentes.objects.create(
            codigo_accidente="VIEW-TEST",
            holding=self.holding,
            empresa=self.empresa,
            centro=self.centro,
            trabajador=self.trabajador,
            usuario_asignado=self.user,
            creado_por=self.user,
        )
        self.client.login(username=self.user.rut, password="admin123")

    def test_home_view(self):
        response = self.client.get(reverse("accidentes:home"))
        self.assertEqual(response.status_code, 200)

    def test_empresa_view(self):
        response = self.client.get(
            reverse("accidentes:empresa", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_trabajador_view(self):
        response = self.client.get(
            reverse("accidentes:trabajador", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_accidente_view(self):
        response = self.client.get(
            reverse("accidentes:accidente", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_declaraciones_view(self):
        response = self.client.get(
            reverse("accidentes:ia_declaraciones", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_relato_view(self):
        response = self.client.get(
            reverse("accidentes:ia_relato", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_hechos_view(self):
        response = self.client.get(
            reverse("accidentes:ia_hechos", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_arbol_view(self):
        response = self.client.get(
            reverse("accidentes:ia_arbol", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_medidas_view(self):
        response = self.client.get(
            reverse("accidentes:ia_medidas", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_documentos_view(self):
        response = self.client.get(
            reverse("accidentes:ia_fotos", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)

    def test_informe_view(self):
        response = self.client.get(
            reverse("accidentes:generar_informe", args=[self.accidente.codigo_accidente])
        )
        self.assertEqual(response.status_code, 200)


class SecurityTests(TestCase):
    """Tests de seguridad — acceso sin autenticación."""

    def test_home_requires_login(self):
        response = self.client.get(reverse("accidentes:home"))
        self.assertEqual(response.status_code, 302)

    def test_login_has_csrf(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_login_has_rut_field(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertContains(response, "RUT")

    def test_admin_login_page(self):
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
