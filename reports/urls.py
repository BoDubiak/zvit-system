from django.urls import path

from . import views

urlpatterns = [
    path("", views.company_reports, name="company_reports"),
    path("reports/<int:pk>/upload/", views.upload_report, name="upload_report"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/reports/<int:pk>/accept/", views.accept_expected_report, name="accept_expected_report"),
    path("dashboard/reports/<int:pk>/reject/", views.reject_expected_report, name="reject_expected_report"),
    path("dashboard/generate/", views.generate_expected_reports_view, name="generate_expected_reports"),
    path("dashboard/export-xlsx/", views.export_control_report, name="export_control_report"),
    path("dashboard/export-zip/", views.export_archives_view, name="export_archives"),
]
