import pytest
from django.core.management import call_command

from users.models import User

pytestmark = pytest.mark.django_db


def run(monkeypatch, capsys, **env):
    for key in ('ADMIN_EMAIL', 'ADMIN_PASSWORD'):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    call_command('create_admin')
    return capsys.readouterr().out


def test_creates_admin_from_environment(monkeypatch, capsys):
    run(monkeypatch, capsys, ADMIN_EMAIL='boss@example.com', ADMIN_PASSWORD='Boss!Pass123')

    admin = User.objects.get(email='boss@example.com')
    assert admin.role == User.ADMIN
    assert admin.is_staff and admin.is_superuser
    assert admin.check_password('Boss!Pass123')


def test_is_safe_to_run_twice_and_updates_password(monkeypatch, capsys):
    run(monkeypatch, capsys, ADMIN_EMAIL='boss@example.com', ADMIN_PASSWORD='First!Pass123')
    output = run(monkeypatch, capsys, ADMIN_EMAIL='boss@example.com', ADMIN_PASSWORD='Second!Pass123')

    assert 'already exists' in output
    assert User.objects.filter(email='boss@example.com').count() == 1
    assert User.objects.get(email='boss@example.com').check_password('Second!Pass123')


def test_skips_without_password(monkeypatch, capsys):
    output = run(monkeypatch, capsys, ADMIN_EMAIL='boss@example.com')

    assert 'skipping' in output
    assert not User.objects.filter(email='boss@example.com').exists()


def test_never_prints_the_password(monkeypatch, capsys):
    output = run(monkeypatch, capsys, ADMIN_EMAIL='boss@example.com', ADMIN_PASSWORD='Hidden!Pass123')
    assert 'Hidden!Pass123' not in output
