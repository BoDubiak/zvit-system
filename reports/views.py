from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .excel import build_control_report
from .forms import ExpectedReportUploadForm, GenerateExpectedReportsForm, RejectReportForm
from .generation import MissingReportFormsError, generate_expected_reports
from .models import ExpectedReport, OrganizationUser, ReportForm, ReportingPeriod
from .permissions import can_manage_reports, manageable_reports, managed_organization_ids
from .services import validate_uploaded_report
from .status_services import accept_report, reject_report
from .zip_export import build_all_periods_archives_bundle, build_archives_bundle


def _user_organizations(user):
    return OrganizationUser.objects.filter(user=user).select_related("organization")


@login_required
def company_reports(request):
    organization_links = _user_organizations(request.user)
    organizations = [link.organization for link in organization_links]
    period_id = request.GET.get("period")
    reports = ExpectedReport.objects.select_related("organization", "period", "form").filter(organization__in=organizations)
    if period_id:
        reports = reports.filter(period_id=period_id)
    periods = ReportingPeriod.objects.order_by("-year", "quarter")
    return render(request, "reports/company_reports.html", {"reports": reports, "periods": periods, "selected_period": period_id})


@login_required
def upload_report(request, pk):
    organization_ids = _user_organizations(request.user).values_list("organization_id", flat=True)
    expected_report = get_object_or_404(
        ExpectedReport.objects.select_related("organization", "period", "form"),
        pk=pk,
        organization_id__in=organization_ids,
    )
    if request.method == "POST":
        form = ExpectedReportUploadForm(request.POST, request.FILES, instance=expected_report)
        if form.is_valid():
            ok, message = validate_uploaded_report(expected_report, form.cleaned_data["uploaded_file"], uploaded_by=request.user)
            if ok:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect("company_reports")
    else:
        form = ExpectedReportUploadForm(instance=expected_report)
    return render(request, "reports/upload_report.html", {"form": form, "expected_report": expected_report})


@user_passes_test(can_manage_reports)
def admin_dashboard(request):
    reports = manageable_reports(request.user).select_related("organization", "period", "form", "uploaded_by")
    period_id = request.GET.get("period")
    status = request.GET.get("status")
    form_id = request.GET.get("form")
    organization_query = request.GET.get("organization")

    if period_id:
        reports = reports.filter(period_id=period_id)
    if status == "missing":
        reports = reports.filter(status=ExpectedReport.Status.PENDING)
    elif status == "errors":
        reports = reports.filter(status__in=[ExpectedReport.Status.ERROR, ExpectedReport.Status.REJECTED])
    elif status == "uploaded":
        reports = reports.filter(status=ExpectedReport.Status.UPLOADED)
    elif status == "accepted":
        reports = reports.filter(status=ExpectedReport.Status.ACCEPTED)
    if form_id:
        reports = reports.filter(form_id=form_id)
    if organization_query:
        reports = reports.filter(organization__name__icontains=organization_query) | reports.filter(organization__edrpou__icontains=organization_query)

    reports = reports.order_by("organization__name", "form__code")
    paginator = Paginator(reports, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "reports/admin_dashboard.html",
        {
            "reports": page_obj.object_list,
            "page_obj": page_obj,
            "querystring": query_params.urlencode(),
            "periods": ReportingPeriod.objects.order_by("-year", "quarter"),
            "forms": ReportForm.objects.filter(is_active=True),
            "filters": request.GET,
        },
    )


@require_POST
@user_passes_test(can_manage_reports)
def accept_expected_report(request, pk):
    report = get_object_or_404(manageable_reports(request.user), pk=pk)
    accept_report(report, changed_by=request.user)
    messages.success(request, "Звіт позначено як прийнятий.")
    return redirect(request.POST.get("next") or "admin_dashboard")


@user_passes_test(can_manage_reports)
def reject_expected_report(request, pk):
    report = get_object_or_404(manageable_reports(request.user), pk=pk)
    next_url = request.POST.get("next") or request.GET.get("next") or "admin_dashboard"
    if request.method == "POST":
        form = RejectReportForm(request.POST)
        if form.is_valid():
            reject_report(report, changed_by=request.user, comment=form.cleaned_data["reason"])
            messages.warning(request, "Звіт позначено як відхилений.")
            return redirect(next_url)
    else:
        form = RejectReportForm()

    return render(request, "reports/reject_report.html", {"form": form, "report": report, "next_url": next_url})


@user_passes_test(can_manage_reports)
def generate_expected_reports_view(request):
    if request.method == "POST":
        form = GenerateExpectedReportsForm(request.POST, user=request.user)
        if form.is_valid():
            organization_ids = list(form.cleaned_data["organizations"].values_list("id", flat=True))
            allowed_organization_ids = managed_organization_ids(request.user)
            if allowed_organization_ids is not None and not organization_ids:
                organization_ids = allowed_organization_ids
            try:
                result = generate_expected_reports(
                    year=form.cleaned_data["year"],
                    quarter=form.cleaned_data["quarter"],
                    organization_ids=organization_ids,
                    form_ids=list(form.cleaned_data["report_forms"].values_list("id", flat=True)),
                )
            except MissingReportFormsError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Очікувані звіти згенеровано для {result.period.year} {result.period.quarter}. "
                    f"Організацій: {result.organizations_count}, форм: {result.forms_count}. "
                    f"Створено: {result.created}, вже існували: {result.existing}.",
                )
                return redirect("admin_dashboard")
    else:
        form = GenerateExpectedReportsForm(user=request.user)

    return render(request, "reports/generate_expected_reports.html", {"form": form})


@user_passes_test(can_manage_reports)
def export_control_report(request):
    period_id = request.GET.get("period")
    period = get_object_or_404(ReportingPeriod, pk=period_id) if period_id else None
    workbook = build_control_report(period, organization_ids=managed_organization_ids(request.user))
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    filename = f"control_report_{period.year}_{period.quarter}.xlsx" if period else "control_report_all_periods.xlsx"
    return FileResponse(buffer, as_attachment=True, filename=filename)


@user_passes_test(can_manage_reports)
def export_archives_view(request):
    period_id = request.GET.get("period")
    organization_ids = managed_organization_ids(request.user)
    if period_id:
        period = get_object_or_404(ReportingPeriod, pk=period_id)
        buffer = BytesIO(build_archives_bundle(period, organization_ids=organization_ids))
        filename = f"archives_{period.year}_{period.quarter}.zip"
    else:
        buffer = BytesIO(build_all_periods_archives_bundle(organization_ids=organization_ids))
        filename = "archives_all_periods.zip"
    return FileResponse(buffer, as_attachment=True, filename=filename)
