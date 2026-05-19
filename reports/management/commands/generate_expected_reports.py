from django.core.management.base import BaseCommand, CommandError

from reports.generation import MissingReportFormsError, generate_expected_reports


class Command(BaseCommand):
    help = "Generate ExpectedReport rows for active organizations for a year and quarter."

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, required=True)
        parser.add_argument("--quarter", choices=["Q1", "Q2", "Q3", "Q4"], required=True)
        parser.add_argument(
            "--include-optional",
            action="store_true",
            help="Also generate optional full-report forms J0900904, J0901005 and J0901301.",
        )

    def handle(self, *args, **options):
        try:
            result = generate_expected_reports(
                year=options["year"],
                quarter=options["quarter"],
                include_optional=options["include_optional"],
            )
        except MissingReportFormsError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Expected reports generated. Created: {result.created}, already existed: {result.existing}"
            )
        )
