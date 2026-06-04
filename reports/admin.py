from django.contrib import admin, messages

from .models import (
    EmailNotification,
    ExpectedReport,
    Organization,
    OrganizationUser,
    ReportForm,
    ReportingPeriod,
    ReportStatusLog,
    ReportUploadLog,
)
from .services import validate_uploaded_report
from .status_services import accept_report, reject_report


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "edrpou", "report_type", "contact_email", "is_active"]
    list_filter = ["report_type", "is_active"]
    search_fields = ["name", "edrpou", "contact_email"]


@admin.register(OrganizationUser)
class OrganizationUserAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role"]
    list_filter = ["role", "organization"]
    search_fields = ["user__username", "user__email", "organization__name", "organization__edrpou"]


@admin.register(ReportForm)
class ReportFormAdmin(admin.ModelAdmin):
    list_display = ["code", "xml_schema", "name", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["code", "xml_schema", "name"]


@admin.register(ReportingPeriod)
class ReportingPeriodAdmin(admin.ModelAdmin):
    list_display = ["year", "quarter", "is_open", "deadline"]
    list_filter = ["year", "quarter", "is_open"]


@admin.action(description="Позначити як прийняті")
def mark_accepted(modeladmin, request, queryset):
    updated = 0
    for report in queryset:
        accept_report(report, changed_by=request.user)
        updated += 1
    messages.success(request, f"Прийнято звітів: {updated}")


@admin.action(description="Позначити як відхилені")
def mark_rejected(modeladmin, request, queryset):
    updated = 0
    for report in queryset:
        reject_report(report, changed_by=request.user)
        updated += 1
    messages.warning(request, f"Відхилено звітів: {updated}")


@admin.register(ExpectedReport)
class ExpectedReportAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "period",
        "form",
        "status",
        "uploaded_at",
        "original_filename",
        "validation_message",
    ]
    list_filter = ["period", "organization", "form", "status"]
    search_fields = ["organization__name", "organization__edrpou", "form__code", "form__xml_schema"]
    readonly_fields = [
        "original_filename",
        "normalized_filename",
        "uploaded_by",
        "uploaded_at",
        "validation_message",
        "created_at",
        "updated_at",
    ]
    actions = [mark_accepted, mark_rejected]

    def save_model(self, request, obj, form, change):
        uploaded_file = form.cleaned_data.get("uploaded_file")
        if uploaded_file and getattr(uploaded_file, "name", None):
            obj.uploaded_by = request.user
            obj.save()
            validate_uploaded_report(obj, uploaded_file, uploaded_by=request.user)
            return
        super().save_model(request, obj, form, change)


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = [
        "subject",
        "organization",
        "period",
        "notification_type",
        "status",
        "attempts",
        "created_at",
        "sent_at",
    ]
    list_filter = ["status", "notification_type", "period", "created_at", "sent_at"]
    search_fields = ["subject", "organization__name", "organization__edrpou", "recipients", "last_error"]
    readonly_fields = [
        "organization",
        "period",
        "notification_type",
        "recipients",
        "subject",
        "body",
        "status",
        "attempts",
        "last_error",
        "created_at",
        "sent_at",
    ]


@admin.register(ReportUploadLog)
class ReportUploadLogAdmin(admin.ModelAdmin):
    list_display = [
        "expected_report",
        "original_filename",
        "uploaded_by",
        "uploaded_at",
        "parsed_edrpou",
        "parsed_year",
        "parsed_quarter",
        "parsed_form",
        "is_valid",
        "message",
    ]
    list_filter = ["is_valid", "parsed_year", "parsed_quarter", "parsed_form"]
    search_fields = ["expected_report__organization__name", "expected_report__organization__edrpou", "original_filename"]
    readonly_fields = [
        "expected_report",
        "file",
        "original_filename",
        "uploaded_by",
        "uploaded_at",
        "parsed_edrpou",
        "parsed_year",
        "parsed_quarter",
        "parsed_form",
        "is_valid",
        "message",
    ]


@admin.register(ReportStatusLog)
class ReportStatusLogAdmin(admin.ModelAdmin):
    list_display = ["expected_report", "changed_by", "old_status", "new_status", "created_at", "comment"]
    list_filter = ["old_status", "new_status", "created_at"]
    search_fields = [
        "expected_report__organization__name",
        "expected_report__organization__edrpou",
        "changed_by__username",
        "comment",
    ]
    readonly_fields = ["expected_report", "changed_by", "old_status", "new_status", "comment", "created_at"]
