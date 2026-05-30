import re
from pathlib import Path
from xml.etree import ElementTree

from django.core.files.base import ContentFile
from django.utils import timezone

from .constants import QUARTER_BY_MONTH
from .models import ExpectedReport, ReportUploadLog, report_upload_path


class XMLParseError(ValueError):
    pass


def _local_name(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _text_by_names(root, names):
    names = set(names)
    for element in root.iter():
        if _local_name(element.tag) in names and element.text:
            return element.text.strip()
    return ""


def _schema_from_location(root):
    for key, value in root.attrib.items():
        if key.endswith("noNamespaceSchemaLocation") and value:
            match = re.search(r"(S\d+)", value)
            if match:
                return match.group(1)
    return ""


def _schema_from_doc_fields(root):
    c_doc = _text_by_names(root, ["C_DOC"])
    c_doc_sub = _text_by_names(root, ["C_DOC_SUB"])
    c_doc_ver = _text_by_names(root, ["C_DOC_VER"])
    if c_doc and c_doc_sub and c_doc_ver:
        return f"S{int(c_doc):02d}{int(c_doc_sub):03d}{int(c_doc_ver):02d}"
    return ""


def parse_financial_xml(file):
    try:
        current_position = file.tell()
    except (AttributeError, OSError):
        current_position = None

    try:
        if hasattr(file, "seek"):
            file.seek(0)
        root = ElementTree.parse(file).getroot()
    except ElementTree.ParseError as exc:
        raise XMLParseError(f"XML не вдалося розпарсити: {exc}") from exc
    finally:
        if current_position is not None and hasattr(file, "seek"):
            file.seek(current_position)

    edrpou = _text_by_names(root, ["TIN", "FIRM_EDRPOU"])
    year_text = _text_by_names(root, ["PERIOD_YEAR"])
    month_text = _text_by_names(root, ["PERIOD_MONTH"])
    quarter = QUARTER_BY_MONTH.get(month_text.lstrip("0") if month_text != "0" else month_text) or QUARTER_BY_MONTH.get(month_text)
    xml_schema = _schema_from_location(root) or _schema_from_doc_fields(root)

    try:
        year = int(year_text)
    except (TypeError, ValueError):
        year = None

    return {
        "edrpou": edrpou,
        "year": year,
        "quarter": quarter or "",
        "xml_schema": xml_schema,
    }


def normalized_report_filename(expected_report):
    return f"{expected_report.organization.edrpou}-{expected_report.period.year}-{expected_report.period.quarter}.XML"


def validate_uploaded_report(expected_report, uploaded_file, uploaded_by=None, accepted=False):
    original_filename = Path(uploaded_file.name).name
    parsed = {}

    if Path(original_filename).suffix.lower() != ".xml":
        message = "Файл має бути у форматі XML"
        _save_failed_upload_log(expected_report, uploaded_file, original_filename, uploaded_by, parsed, message)
        _mark_invalid(expected_report, message, ExpectedReport.Status.ERROR)
        return False, message

    try:
        parsed = parse_financial_xml(uploaded_file)
    except XMLParseError as exc:
        message = str(exc)
        _save_failed_upload_log(expected_report, uploaded_file, original_filename, uploaded_by, parsed, message)
        _mark_invalid(expected_report, message, ExpectedReport.Status.ERROR)
        return False, message

    checks = [
        (parsed.get("edrpou") == expected_report.organization.edrpou, f"Очікується ЄДРПОУ {expected_report.organization.edrpou}, але у файлі {parsed.get('edrpou') or 'не знайдено'}"),
        (parsed.get("year") == expected_report.period.year, f"Очікується рік {expected_report.period.year}, але у файлі {parsed.get('year') or 'не знайдено'}"),
        (parsed.get("quarter") == expected_report.period.quarter, f"Очікується квартал {expected_report.period.quarter}, але у файлі {parsed.get('quarter') or 'не знайдено'}"),
        (parsed.get("xml_schema") == expected_report.form.xml_schema, f"Очікується форма {expected_report.form.xml_schema}, але у файлі {parsed.get('xml_schema') or 'не знайдено'}"),
    ]

    for is_valid, message in checks:
        if not is_valid:
            _save_failed_upload_log(expected_report, uploaded_file, original_filename, uploaded_by, parsed, message)
            _mark_invalid(expected_report, message, ExpectedReport.Status.REJECTED)
            return False, message

    filename = normalized_report_filename(expected_report)
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    content = uploaded_file.read()
    storage = expected_report.uploaded_file.storage
    target_name = report_upload_path(expected_report, filename)
    current_name = expected_report.uploaded_file.name
    if current_name and current_name != target_name:
        storage.delete(current_name)
    if storage.exists(target_name):
        storage.delete(target_name)
    expected_report.uploaded_file.save(filename, ContentFile(content), save=False)
    expected_report.original_filename = original_filename
    expected_report.normalized_filename = filename
    expected_report.uploaded_by = uploaded_by
    expected_report.uploaded_at = timezone.now()
    expected_report.status = ExpectedReport.Status.ACCEPTED if accepted else ExpectedReport.Status.UPLOADED
    expected_report.validation_message = "Файл успішно перевірено"
    expected_report.save()

    ReportUploadLog.objects.create(
        expected_report=expected_report,
        file=ContentFile(content, name=original_filename),
        original_filename=original_filename,
        uploaded_by=uploaded_by,
        parsed_edrpou=parsed.get("edrpou", ""),
        parsed_year=parsed.get("year"),
        parsed_quarter=parsed.get("quarter", ""),
        parsed_form=parsed.get("xml_schema", ""),
        is_valid=True,
        message="Файл успішно перевірено",
    )
    return True, "Файл успішно перевірено"


def _mark_invalid(expected_report, message, status):
    expected_report.status = status
    expected_report.validation_message = message
    expected_report.save(update_fields=["status", "validation_message", "updated_at"])


def _save_failed_upload_log(expected_report, uploaded_file, original_filename, uploaded_by, parsed, message):
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    content = uploaded_file.read()
    ReportUploadLog.objects.create(
        expected_report=expected_report,
        file=ContentFile(content, name=original_filename),
        original_filename=original_filename,
        uploaded_by=uploaded_by,
        parsed_edrpou=parsed.get("edrpou", ""),
        parsed_year=parsed.get("year"),
        parsed_quarter=parsed.get("quarter", ""),
        parsed_form=parsed.get("xml_schema", ""),
        is_valid=False,
        message=message,
    )
