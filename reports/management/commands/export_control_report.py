from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from reports.excel import build_control_report
from reports.models import ReportingPeriod


class Command(BaseCommand):
    help = "Export Excel control report for selected period."

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, required=True)
        parser.add_argument("--quarter", choices=["Q1", "Q2", "Q3", "Q4"], required=True)
        parser.add_argument("--output-dir", default=None)

    def handle(self, *args, **options):
        try:
            period = ReportingPeriod.objects.get(year=options["year"], quarter=options["quarter"])
        except ReportingPeriod.DoesNotExist as exc:
            raise CommandError("ReportingPeriod does not exist") from exc

        output_dir = Path(options["output_dir"] or settings.BASE_DIR / "exports")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"control_report_{period.year}_{period.quarter}.xlsx"
        workbook = build_control_report(period)
        workbook.save(output_file)
        self.stdout.write(self.style.SUCCESS(f"Excel exported: {output_file}"))
