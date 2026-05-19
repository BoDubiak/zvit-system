from django.conf import settings
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    class ReportType(models.TextChoices):
        SMALL = "small", "Мала звітність"
        FULL = "full", "Повна звітність"

    name = models.CharField(max_length=255)
    edrpou = models.CharField(max_length=12, unique=True)
    report_type = models.CharField(max_length=10, choices=ReportType.choices)
    contact_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.edrpou})"


class OrganizationUser(models.Model):
    class Role(models.TextChoices):
        REPRESENTATIVE = "representative", "Представник"
        ADMIN = "admin", "Адміністратор"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization_links")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="user_links")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REPRESENTATIVE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "organization"], name="unique_user_organization")
        ]

    def __str__(self):
        return f"{self.user} -> {self.organization}"


class ReportForm(models.Model):
    code = models.CharField(max_length=20, unique=True)
    xml_schema = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} / {self.xml_schema}"


class ReportingPeriod(models.Model):
    class Quarter(models.TextChoices):
        Q1 = "Q1", "Q1"
        Q2 = "Q2", "Q2"
        Q3 = "Q3", "Q3"
        Q4 = "Q4", "Q4"

    year = models.PositiveIntegerField()
    quarter = models.CharField(max_length=2, choices=Quarter.choices)
    is_open = models.BooleanField(default=True)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year", "quarter"]
        constraints = [
            models.UniqueConstraint(fields=["year", "quarter"], name="unique_reporting_period")
        ]

    def __str__(self):
        return f"{self.year} {self.quarter}"


def report_upload_path(instance, filename):
    return f"reports/{instance.period.year}/{instance.period.quarter}/{instance.organization.edrpou}/{filename}"


def log_upload_path(instance, filename):
    report = instance.expected_report
    ts = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"upload_logs/{report.period.year}/{report.period.quarter}/{report.organization.edrpou}/{ts}_{filename}"


class ExpectedReport(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Очікується"
        UPLOADED = "uploaded", "Завантажено"
        ACCEPTED = "accepted", "Прийнято"
        REJECTED = "rejected", "Відхилено"
        ERROR = "error", "Помилка"

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="expected_reports")
    period = models.ForeignKey(ReportingPeriod, on_delete=models.CASCADE, related_name="expected_reports")
    form = models.ForeignKey(ReportForm, on_delete=models.PROTECT, related_name="expected_reports")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    uploaded_file = models.FileField(upload_to=report_upload_path, blank=True)
    original_filename = models.CharField(max_length=255, blank=True)
    normalized_filename = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_reports",
    )
    uploaded_at = models.DateTimeField(null=True, blank=True)
    validation_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["organization__name", "form__code"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "period", "form"], name="unique_expected_report")
        ]

    def __str__(self):
        return f"{self.organization} - {self.period} - {self.form}"


class ReportUploadLog(models.Model):
    expected_report = models.ForeignKey(ExpectedReport, on_delete=models.CASCADE, related_name="upload_logs")
    file = models.FileField(upload_to=log_upload_path)
    original_filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="report_upload_logs",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_edrpou = models.CharField(max_length=12, blank=True)
    parsed_year = models.PositiveIntegerField(null=True, blank=True)
    parsed_quarter = models.CharField(max_length=2, blank=True)
    parsed_form = models.CharField(max_length=20, blank=True)
    is_valid = models.BooleanField(default=False)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.expected_report_id} {self.original_filename}"


class ReportStatusLog(models.Model):
    expected_report = models.ForeignKey(ExpectedReport, on_delete=models.CASCADE, related_name="status_logs")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="report_status_logs",
    )
    old_status = models.CharField(max_length=20, choices=ExpectedReport.Status.choices)
    new_status = models.CharField(max_length=20, choices=ExpectedReport.Status.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.expected_report_id}: {self.old_status} -> {self.new_status}"
