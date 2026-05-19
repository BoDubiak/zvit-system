import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportStatusLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "old_status",
                    models.CharField(
                        choices=[
                            ("pending", "Очікується"),
                            ("uploaded", "Завантажено"),
                            ("accepted", "Прийнято"),
                            ("rejected", "Відхилено"),
                            ("error", "Помилка"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "new_status",
                    models.CharField(
                        choices=[
                            ("pending", "Очікується"),
                            ("uploaded", "Завантажено"),
                            ("accepted", "Прийнято"),
                            ("rejected", "Відхилено"),
                            ("error", "Помилка"),
                        ],
                        max_length=20,
                    ),
                ),
                ("comment", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="report_status_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "expected_report",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_logs",
                        to="reports.expectedreport",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
