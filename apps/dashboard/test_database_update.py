from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.imports.models import ImportBatch


@pytest.mark.django_db
def test_only_administrator_can_start_database_update(client):
    manager = User.objects.create_user(username="manager", password="test", role=User.Role.MANAGER)
    client.force_login(manager)
    assert "Atualizar base de dados" not in client.get(reverse("home")).content.decode()
    assert client.post(reverse("update-database")).status_code == 403

    administrator = User.objects.create_user(username="admin", password="test", role=User.Role.ADMINISTRATOR)
    client.force_login(administrator)
    assert "Atualizar base de dados" in client.get(reverse("home")).content.decode()
    assert client.get(reverse("update-database")).status_code == 405
    with patch("apps.dashboard.views.collect_from_legacy_database") as task:
        response = client.post(reverse("update-database"))
    assert response.status_code == 302
    task.delay.assert_called_once_with()


@pytest.mark.django_db
def test_database_update_is_disabled_while_collection_runs(client):
    administrator = User.objects.create_user(username="admin", password="test", role=User.Role.ADMINISTRATOR)
    client.force_login(administrator)
    ImportBatch.objects.create(source=ImportBatch.Source.LEGACY, status=ImportBatch.Status.PROCESSING)

    assert "Coleta em andamento desde" in client.get(reverse("home")).content.decode()
    with patch("apps.dashboard.views.collect_from_legacy_database") as task:
        response = client.post(reverse("update-database"))
    assert response.status_code == 302
    task.delay.assert_not_called()


@pytest.mark.django_db
def test_home_shows_failed_attempt_separately_from_last_success(client):
    administrator = User.objects.create_user(username="admin", password="test", role=User.Role.ADMINISTRATOR)
    client.force_login(administrator)
    completed_at = timezone.make_aware(datetime(2026, 10, 30, 14, 52))
    failed_at = timezone.make_aware(datetime(2026, 11, 3, 14, 28))
    ImportBatch.objects.create(
        source=ImportBatch.Source.LEGACY, status=ImportBatch.Status.COMPLETED,
        finished_at=completed_at, imported_rows=140326,
    )
    ImportBatch.objects.create(
        source=ImportBatch.Source.LEGACY, status=ImportBatch.Status.FAILED,
        finished_at=failed_at, error_message="Unable to connect: Connection timed out",
    )

    response = client.get(reverse("home"))

    assert response.context["last_update"] == completed_at
    assert "Última atualização concluída: 30/10/2026 14:52" in response.content.decode()
    assert "Tentativa de 03/11/2026 14:28 falhou." in response.content.decode()
    assert "Não foi possível conectar ao banco de origem." in response.content.decode()


@pytest.mark.django_db
def test_eager_task_failure_is_not_reported_as_started(client):
    administrator = User.objects.create_user(username="admin", password="test", role=User.Role.ADMINISTRATOR)
    client.force_login(administrator)
    with patch("apps.dashboard.views.collect_from_legacy_database") as task:
        task.delay.return_value = SimpleNamespace(state="FAILURE")
        response = client.post(reverse("update-database"), follow=True)

    assert "A atualização falhou." in response.content.decode()
    assert "Atualização da base de dados iniciada" not in response.content.decode()
