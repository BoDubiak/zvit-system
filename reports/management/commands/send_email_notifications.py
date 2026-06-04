from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from reports.models import EmailNotification


class Command(BaseCommand):
    help = "Send queued email notifications."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--max-attempts", type=int, default=3)
        parser.add_argument("--retry-failed", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"]
        max_attempts = options["max_attempts"]
        retry_failed = options["retry_failed"]

        status_filter = Q(status=EmailNotification.Status.PENDING)
        if retry_failed:
            status_filter |= Q(status=EmailNotification.Status.FAILED, attempts__lt=max_attempts)

        with transaction.atomic():
            notifications = list(
                EmailNotification.objects.select_for_update()
                .filter(status_filter)
                .order_by("created_at")[:limit]
            )
            notification_ids = [notification.id for notification in notifications]
            EmailNotification.objects.filter(id__in=notification_ids).update(
                status=EmailNotification.Status.SENDING,
                last_error="",
            )

        sent = 0
        failed = 0
        for notification in notifications:
            try:
                message = EmailMessage(
                    subject=notification.subject,
                    body=notification.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=notification.recipients,
                )
                message.send(fail_silently=False)
            except Exception as exc:  # noqa: BLE001
                notification.status = EmailNotification.Status.FAILED
                notification.attempts += 1
                notification.last_error = str(exc)
                notification.save(update_fields=["status", "attempts", "last_error"])
                failed += 1
            else:
                notification.status = EmailNotification.Status.SENT
                notification.attempts += 1
                notification.sent_at = timezone.now()
                notification.last_error = ""
                notification.save(update_fields=["status", "attempts", "sent_at", "last_error"])
                sent += 1

        self.stdout.write(self.style.SUCCESS(f"Sent: {sent}. Failed: {failed}."))
