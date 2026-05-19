from dataclasses import dataclass

from .constants import FULL_OPTIONAL_REPORT_SCHEMAS, FULL_REQUIRED_REPORT_SCHEMAS, SMALL_REPORT_SCHEMA
from .models import ExpectedReport, Organization, ReportForm, ReportingPeriod


@dataclass(frozen=True)
class GenerateExpectedReportsResult:
    period: ReportingPeriod
    created: int
    existing: int
    organizations_count: int
    forms_count: int


class MissingReportFormsError(ValueError):
    pass


def generate_expected_reports(year, quarter, include_optional=False, organization_ids=None, form_ids=None):
    period, _ = ReportingPeriod.objects.get_or_create(year=year, quarter=quarter)
    forms_by_schema = {form.xml_schema: form for form in ReportForm.objects.filter(is_active=True)}
    selected_forms = list(ReportForm.objects.filter(is_active=True, id__in=form_ids or []))

    full_schemas = list(FULL_REQUIRED_REPORT_SCHEMAS)
    if include_optional:
        full_schemas.extend(FULL_OPTIONAL_REPORT_SCHEMAS)

    if selected_forms:
        selected_schemas = [form.xml_schema for form in selected_forms]
    else:
        selected_schemas = []
        missing = [SMALL_REPORT_SCHEMA, *full_schemas]
        missing = [schema for schema in missing if schema not in forms_by_schema]
        if missing:
            raise MissingReportFormsError(
                f"Missing ReportForm rows for schemas: {', '.join(missing)}. Run seed_report_forms first."
            )

    created = 0
    existing = 0
    organizations = Organization.objects.filter(is_active=True)
    if organization_ids:
        organizations = organizations.filter(id__in=organization_ids)

    used_schema_count = set()
    organization_count = 0
    for organization in organizations:
        organization_count += 1
        schemas = selected_schemas or (
            [SMALL_REPORT_SCHEMA] if organization.report_type == Organization.ReportType.SMALL else full_schemas
        )
        used_schema_count.update(schemas)
        for schema in schemas:
            _, was_created = ExpectedReport.objects.get_or_create(
                organization=organization,
                period=period,
                form=forms_by_schema[schema],
            )
            if was_created:
                created += 1
            else:
                existing += 1

    return GenerateExpectedReportsResult(
        period=period,
        created=created,
        existing=existing,
        organizations_count=organization_count,
        forms_count=len(used_schema_count),
    )
