# Generated manually for the MVP project.

import django.db.models.deletion
import reports.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("edrpou", models.CharField(max_length=12, unique=True)),
                ("report_type", models.CharField(choices=[("small", "Мала звітність"), ("full", "Повна звітність")], max_length=10)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="ReportForm",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True)),
                ("xml_schema", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["code"]},
        ),
        migrations.CreateModel(
            name="ReportingPeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveIntegerField()),
                ("quarter", models.CharField(choices=[("Q1", "Q1"), ("Q2", "Q2"), ("Q3", "Q3"), ("Q4", "Q4")], max_length=2)),
                ("is_open", models.BooleanField(default=True)),
                ("deadline", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-year", "quarter"]},
        ),
        migrations.CreateModel(
            name="ExpectedReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Очікується"), ("uploaded", "Завантажено"), ("accepted", "Прийнято"), ("rejected", "Відхилено"), ("error", "Помилка")], default="pending", max_length=20)),
                ("uploaded_file", models.FileField(blank=True, upload_to=reports.models.report_upload_path)),
                ("original_filename", models.CharField(blank=True, max_length=255)),
                ("normalized_filename", models.CharField(blank=True, max_length=255)),
                ("uploaded_at", models.DateTimeField(blank=True, null=True)),
                ("validation_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("form", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="expected_reports", to="reports.reportform")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expected_reports", to="reports.organization")),
                ("period", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="expected_reports", to="reports.reportingperiod")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="uploaded_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["organization__name", "form__code"]},
        ),
        migrations.CreateModel(
            name="OrganizationUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("representative", "Представник"), ("admin", "Адміністратор")], default="representative", max_length=20)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_links", to="reports.organization")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="organization_links", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="ReportUploadLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to=reports.models.log_upload_path)),
                ("original_filename", models.CharField(max_length=255)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("parsed_edrpou", models.CharField(blank=True, max_length=12)),
                ("parsed_year", models.PositiveIntegerField(blank=True, null=True)),
                ("parsed_quarter", models.CharField(blank=True, max_length=2)),
                ("parsed_form", models.CharField(blank=True, max_length=20)),
                ("is_valid", models.BooleanField(default=False)),
                ("message", models.TextField(blank=True)),
                ("expected_report", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="upload_logs", to="reports.expectedreport")),
                ("uploaded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="report_upload_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.AddConstraint(
            model_name="reportingperiod",
            constraint=models.UniqueConstraint(fields=("year", "quarter"), name="unique_reporting_period"),
        ),
        migrations.AddConstraint(
            model_name="expectedreport",
            constraint=models.UniqueConstraint(fields=("organization", "period", "form"), name="unique_expected_report"),
        ),
        migrations.AddConstraint(
            model_name="organizationuser",
            constraint=models.UniqueConstraint(fields=("user", "organization"), name="unique_user_organization"),
        ),
    ]
