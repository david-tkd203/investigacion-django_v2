#!/bin/sh
set -e

# Esperar base de datos (MySQL)
if [ -n "${DB_WAIT_SECONDS:-}" ]; then
    echo ">>> Esperando ${DB_WAIT_SECONDS}s por base de datos..."
    sleep "${DB_WAIT_SECONDS}"
fi

echo ">>> Ejecutando migraciones..."
python manage.py migrate --noinput

echo ">>> Recolectando estáticos..."
python manage.py collectstatic --noinput --clear 2>/dev/null || python manage.py collectstatic --noinput

echo ">>> Restableciendo contraseña admin..."
python manage.py shell -c "
from accounts.models import User
u = User.objects.filter(is_superuser=True).first()
if u:
    u.set_password('admin123')
    u.save()
    print(f'  Password restablecido para {u.username}')
else:
    print('  No hay superuser, se omite')
" 2>/dev/null || true

echo ">>> Iniciando servidor..."
exec "$@"
