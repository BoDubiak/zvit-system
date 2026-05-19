from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings

from .models import ExpectedReport, ReportingPeriod


def export_archives(period, output_dir=None):
    output_path = Path(output_dir or settings.BASE_DIR / "exports" / f"{period.year}_{period.quarter}")
    output_path.mkdir(parents=True, exist_ok=True)

    created = []
    forms = period.expected_reports.select_related("form").values("form__code").distinct()
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
        with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
            for report in reports:
                inner_name = report.normalized_filename or f"{report.organization.edrpou}-{period.year}-{period.quarter}.XML"
                archive.write(report.uploaded_file.path, arcname=inner_name)
        created.append(archive_path)
    return created


def build_archives_bundle(period):
    with TemporaryDirectory() as tmpdir:
        archive_paths = export_archives(period, output_dir=tmpdir)
        bundle_path = Path(tmpdir) / f"archives_{period.year}_{period.quarter}.zip"
        with ZipFile(bundle_path, "w", ZIP_DEFLATED) as bundle:
            for archive_path in archive_paths:
                bundle.write(archive_path, arcname=archive_path.name)
        return bundle_path.read_bytes()


def build_all_periods_archives_bundle():
    periods = ReportingPeriod.objects.filter(expected_reports__uploaded_file__gt="").distinct().order_by("year", "quarter")
    with TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        bundle_path = root_path / "archives_all_periods.zip"
        with ZipFile(bundle_path, "w", ZIP_DEFLATED) as bundle:
            for period in periods:
                period_dir = root_path / f"{period.year}_{period.quarter}"
                archive_paths = export_archives(period, output_dir=period_dir)
                for archive_path in archive_paths:
                    bundle.write(archive_path, arcname=f"{period.year}_{period.quarter}/{archive_path.name}")
        return bundle_path.read_bytes()
