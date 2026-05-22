from django.core.exceptions import ValidationError

from .models import ExpectedReport, ReportStatusLog


def change_report_status(expected_report, new_status, changed_by=None, comment=""):
    old_status = expected_report.status
    expected_report.status = new_status
    expected_report.validation_message = comment
    expected_report.save(update_fields=["status", "validation_message", "updated_at"])

    ReportStatusLog.objects.create(
        expected_report=expected_report,
        changed_by=changed_by if getattr(changed_by, "is_authenticated", False) else None,
        old_status=old_status,
        new_status=new_status,
        comment=comment,
    )
    return expected_report


def accept_report(expected_report, changed_by=None, comment="Звіт прийнято адміністратором"):
    if expected_report.status != ExpectedReport.Status.UPLOADED or not expected_report.uploaded_file:
        raise ValidationError("Прийняти можна тільки завантажений звіт із файлом.")
    return change_report_status(
        expected_report=expected_report,
        new_status=ExpectedReport.Status.ACCEPTED,
        changed_by=changed_by,
        comment=comment,
    )


def reject_report(expected_report, changed_by=None, comment="Звіт відхилено адміністратором"):
    return change_report_status(
        expected_report=expected_report,
        new_status=ExpectedReport.Status.REJECTED,
        changed_by=changed_by,
        comment=comment,
    )
