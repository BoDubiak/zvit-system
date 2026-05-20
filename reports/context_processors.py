from .permissions import can_manage_reports


def report_permissions(request):
    return {"can_manage_reports": can_manage_reports(request.user)}
