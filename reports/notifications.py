from collections import defaultdict

from .models import EmailNotification, OrganizationUser


def organization_notification_recipients(organization):
    recipients = set()
    if organization.contact_email:
        recipients.add(organization.contact_email)

    user_emails = (
        OrganizationUser.objects.filter(organization=organization)
        .exclude(user__email="")
        .values_list("user__email", flat=True)
    )
    recipients.update(email for email in user_emails if email)

    return sorted(recipients)


def queue_expected_reports_created_notifications(expected_reports):
    reports_by_organization = defaultdict(list)
    for report in expected_reports:
        reports_by_organization[report.organization_id].append(report)

    notifications = []
    for reports in reports_by_organization.values():
        first_report = reports[0]
        organization = first_report.organization
        period = first_report.period
        recipients = organization_notification_recipients(organization)
        if not recipients:
            continue

        forms = "\n".join(
            f"- {report.form.code}: {report.form.name}"
            for report in sorted(reports, key=lambda item: item.form.code)
        )
        subject = f"Нові завдання зі звітності: {period.year} {period.quarter}"
        body = (
            f"У вашому кабінеті з'явилися нові завдання для організації "
            f"{organization.name} ({organization.edrpou}).\n\n"
            f"Період: {period.year} {period.quarter}\n\n"
            f"Форми:\n{forms}\n\n"
            f"Будь ласка, увійдіть у кабінет для завантаження звітів."
        )
        notifications.append(
            EmailNotification(
                organization=organization,
                period=period,
                notification_type=EmailNotification.Type.EXPECTED_REPORTS_CREATED,
                recipients=recipients,
                subject=subject,
                body=body,
            )
        )

    if notifications:
        EmailNotification.objects.bulk_create(notifications)

    return notifications
