from .models import ExpectedReport, Organization, OrganizationUser


def can_manage_reports(user):
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_staff:
        return True
    return OrganizationUser.objects.filter(user=user, role=OrganizationUser.Role.ADMIN).exists()


def managed_organization_ids(user):
    if not getattr(user, "is_authenticated", False):
        return []
    if user.is_staff:
        return None
    return list(
        OrganizationUser.objects.filter(user=user, role=OrganizationUser.Role.ADMIN).values_list(
            "organization_id",
            flat=True,
        )
    )


def managed_organizations(user):
    organization_ids = managed_organization_ids(user)
    organizations = Organization.objects.filter(is_active=True)
    if organization_ids is None:
        return organizations
    return organizations.filter(id__in=organization_ids)


def manageable_reports(user):
    reports = ExpectedReport.objects.all()
    organization_ids = managed_organization_ids(user)
    if organization_ids is None:
        return reports
    return reports.filter(organization_id__in=organization_ids)
