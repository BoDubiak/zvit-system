from django.core.management.base import BaseCommand

from reports.constants import DEFAULT_REPORT_FORMS
from reports.models import ReportForm


class Command(BaseCommand):
    help = "Create or update default financial report forms."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for item in DEFAULT_REPORT_FORMS:
            _, was_created = ReportForm.objects.update_or_create(
                xml_schema=item["xml_schema"],
                defaults={
                    "code": item["code"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Report forms seeded. Created: {created}, updated: {updated}"))
