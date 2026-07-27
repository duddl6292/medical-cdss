"""Prepare the isolated PoC schema and run Django migrations."""

import os
import re

from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection
from psycopg import sql


IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def _identifier(name: str, setting: str) -> str:
    if IDENTIFIER.fullmatch(name) is None:
        raise CommandError(f"{setting} is not a safe PostgreSQL identifier.")
    return name


class Command(BaseCommand):
    help = "Create the isolated PoC schema, grant app access, and migrate."

    def handle(self, *args, **options):
        schema = _identifier(
            os.environ.get("DB_SCHEMA", "medical_cdss"),
            "DB_SCHEMA",
        )
        app_user = _identifier(
            os.environ.get("DB_APP_USER", "medical_cdss_app"),
            "DB_APP_USER",
        )

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(schema)
                )
            )
            cursor.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema),
                    sql.Identifier(app_user),
                )
            )
            cursor.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA {} "
                    "GRANT SELECT, INSERT, UPDATE, DELETE "
                    "ON TABLES TO {}"
                ).format(
                    sql.Identifier(schema),
                    sql.Identifier(app_user),
                )
            )
            cursor.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA {} "
                    "GRANT USAGE, SELECT ON SEQUENCES TO {}"
                ).format(
                    sql.Identifier(schema),
                    sql.Identifier(app_user),
                )
            )

        call_command("migrate", interactive=False)

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL(
                    "GRANT SELECT, INSERT, UPDATE, DELETE "
                    "ON ALL TABLES IN SCHEMA {} TO {}"
                ).format(
                    sql.Identifier(schema),
                    sql.Identifier(app_user),
                )
            )
            cursor.execute(
                sql.SQL(
                    "GRANT USAGE, SELECT ON ALL SEQUENCES "
                    "IN SCHEMA {} TO {}"
                ).format(
                    sql.Identifier(schema),
                    sql.Identifier(app_user),
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Migrated schema '{schema}' and granted runtime access."
            )
        )
