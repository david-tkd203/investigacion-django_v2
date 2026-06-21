"""
Tests de autenticación — accounts app.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import normaliza_rut, valida_rut_chile
from accidentes.constants import ROLE_INVESTIGADOR

User = get_user_model()


class RutValidationTests(TestCase):
    def test_normaliza_rut_with_dots_and_dash(self):
        self.assertEqual(normaliza_rut("12.345.678-5"), "12345678-5")

    def test_normaliza_rut_without_format(self):
        self.assertEqual(normaliza_rut("12345678-5"), "12345678-5")

    def test_normaliza_rut_uppercase_k(self):
        self.assertEqual(normaliza_rut("12.345.678-k"), "12345678-K")

    def test_normaliza_rut_none(self):
        self.assertIsNone(normaliza_rut(None))

    def test_valida_rut_valido(self):
        # RUT con DV correcto (módulo 11)
        self.assertTrue(valida_rut_chile("11111111-1"))

    def test_valida_rut_invalido_dv(self):
        self.assertFalse(valida_rut_chile("11111111-2"))

    def test_valida_rut_formato_incorrecto(self):
        self.assertFalse(valida_rut_chile("1234"))

    def test_valida_rut_vacio(self):
        self.assertFalse(valida_rut_chile(""))


class RutAuthBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            rut="12345678-5",
            password="testpass123",
            email="test@example.com",
            is_active=True,
        )

    def test_login_valid_rut(self):
        login = self.client.login(username="12345678-5", password="testpass123")
        self.assertTrue(login)

    def test_login_invalid_password(self):
        login = self.client.login(username="12345678-5", password="wrongpass")
        self.assertFalse(login)

    def test_login_invalid_rut(self):
        login = self.client.login(username="00000000-0", password="testpass123")
        self.assertFalse(login)


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            rut="12345678-5",
            password="testpass123",
            email="test@example.com",
            is_active=True,
        )

    def test_login_page_status(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_login_post_success(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "12345678-5",
            "password": "testpass123",
        })
        self.assertIn(response.status_code, [302, 200])

    def test_login_post_failure(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "12345678-5",
            "password": "wrongpass",
        })
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username="12345678-5", password="testpass123")
        response = self.client.post(reverse("accounts:logout"))
        self.assertIn(response.status_code, [302, 200])


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testmodel",
            rut="9876543-2",
            password="pass123",
            email="model@test.com",
            first_name="Test",
            last_name="User",
        )

    def test_user_str(self):
        self.assertIsNotNone(str(self.user))

    def test_user_rut_field(self):
        self.assertEqual(self.user.rut, "9876543-2")

    def test_user_rol_default(self):
        self.assertEqual(self.user.rol, ROLE_INVESTIGADOR)

    def test_user_team_default(self):
        self.assertEqual(self.user.team, "adherente")


class RutPasswordResetFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            rut="12345678-5",
            password="pass123",
            email="reset@test.com",
            is_active=True,
        )

    def test_password_reset_page(self):
        response = self.client.get(reverse("accounts:password_reset"))
        self.assertEqual(response.status_code, 200)

    def test_password_change_page_requires_login(self):
        response = self.client.get(reverse("accounts:password_change"))
        self.assertEqual(response.status_code, 302)
