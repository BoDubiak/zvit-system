from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings

from .models import ExpectedReport


def export_archives(period, output_dir=None, organization_ids=None):
    output_path = Path(output_dir or settings.BASE_DIR / "exports" / f"{period.year}_{period.quarter}")
    output_path.mkdir(parents=True, exist_ok=True)

    created = []
    expected_reports = period.expected_reports.select_related("form")
    if organization_ids is not None:
        expected_reports = expected_reports.filter(organization_id__in=organization_ids)
    forms = expected_reports.values("form__code").distinct()
    for item in forms:
        code = item["form__code"]
        archive_path = output_path / f"{code}.zip"
        reports = (
            ExpectedReport.objects.select_related("organization", "period", "form")
            .filter(
                period=period,
                form__code=code,
                status__in=[ExpectedReport.Status.ACCEPTED, ExpectedReport.Status.UPLOADED],
            )
            .exclude(uploaded_file="")
        )
        if organization_ids is not None:
            reports = reports.filter(organization_id__in=organization_ids)
        with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
            for report in reports:
                inner_name = report.normalized_filename or f"{report.organization.edrpou}-{period.year}-{period.quarter}.XML"
                archive.write(report.uploaded_file.path, arcname=inner_name)
        created.append(archive_path)
    return created


def build_archives_bundle(period, organization_ids=None):
    with TemporaryDirectory() as tmpdir:
        archive_paths = export_archives(period, output_dir=tmpdir, organization_ids=organization_ids)
        bundle_path = Path(tmpdir) / f"archives_{period.year}_{period.quarter}.zip"
        with ZipFile(bundle_path, "w", ZIP_DEFLATED) as bundle:
            for archive_path in archive_paths:
                bundle.write(archive_path, arcname=archive_path.name)
        return bundle_path.read_bytes()


def build_all_periods_archives_bundle(organization_ids=None):
    reports = (
        ExpectedReport.objects.select_related("organization", "period", "form")
        .filter(
            status__in=[ExpectedReport.Status.ACCEPTED, ExpectedReport.Status.UPLOADED],
        )
        .exclude(uploaded_file="")
    )
    if organization_ids is not None:
        reports = reports.filter(organization_id__in=organization_ids)
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        bundle_path = root_path / "archives_all_periods.zip"
        with ZipFile(bundle_path, "w", ZIP_DEFLATED) as bundle:
            for code in reports.values_list("form__code", flat=True).distinct():
                archive_path = root_path / f"{code}.zip"
                with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
                    for report in reports.filter(form__code=code):
                        inner_name = report.normalized_filename or (
                            f"{report.organization.edrpou}-{report.period.year}-{report.period.quarter}.XML"
                        )
                        archive.write(report.uploaded_file.path, arcname=inner_name)
                bundle.write(archive_path, arcname=archive_path.name)
        return bundle_path.read_bytes()
