from django.core.management.base import BaseCommand, CommandError

from reports.models import ReportingPeriod
from reports.zip_export import export_archives


class Command(BaseCommand):
    help = "Create ZIP archives by report form code for selected period."

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, required=True)
        parser.add_argument("--quarter", choices=["Q1", "Q2", "Q3", "Q4"], required=True)
        parser.add_argument("--output-dir", default=None)

    def handle(self, *args, **options):
        try:
            period = ReportingPeriod.objects.get(year=options["year"], quarter=options["quarter"])
        except ReportingPeriod.DoesNotExist as exc:
            raise CommandError("ReportingPeriod does not exist") from exc

        archives = export_archives(period, output_dir=options["output_dir"])
        for archive in archives:
            self.stdout.write(str(archive))
        self.stdout.write(self.style.SUCCESS(f"Archives exported: {len(archives)}"))
