from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from invoice_db.db import connection
from invoice_db.services import workspaces as workspace_services


class Command(BaseCommand):
    help = "Delete expired guest workspaces and their temporary users."

    def handle(self, *args, **options):
        with connection.db_session(connection.DB_PATH) as (connect, cursor):
            owner_user_ids = workspace_services.delete_expired_guest_workspaces(cursor)

        if owner_user_ids:
            User = get_user_model()
            User.objects.filter(id__in=owner_user_ids).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {len(owner_user_ids)} expired guest workspace(s)."
            )
        )
