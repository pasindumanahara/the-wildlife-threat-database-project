from pathlib import Path

import sqlparse
from django.db import migrations


def apply_schema(apps, schema_editor):
    schema_path = Path(__file__).resolve().parents[3] / 'database' / '001_initial_schema.sql'
    for statement in sqlparse.split(schema_path.read_text(encoding='utf-8')):
        if statement.strip():
            schema_editor.execute(statement)


class Migration(migrations.Migration):
    initial = True
    operations = [migrations.RunPython(apply_schema, migrations.RunPython.noop)]
