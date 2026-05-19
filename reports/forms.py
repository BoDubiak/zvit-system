from django import forms as django_forms

from .models import ExpectedReport, Organization, ReportForm, ReportingPeriod


class ExpectedReportUploadForm(django_forms.ModelForm):
    class Meta:
        model = ExpectedReport
        fields = ["uploaded_file"]
        widgets = {"uploaded_file": django_forms.ClearableFileInput(attrs={"accept": ".xml"})}


class DashboardFilterForm(django_forms.Form):
    period = django_forms.IntegerField(required=False)
    status = django_forms.ChoiceField(
        required=False,
        choices=[
            ("", "Усі статуси"),
            ("missing", "Тільки відсутні"),
            ("errors", "Тільки помилки"),
            ("uploaded", "Тільки завантажені"),
            ("accepted", "Тільки прийняті"),
        ],
    )
    form = django_forms.IntegerField(required=False)
    organization = django_forms.CharField(required=False)


class GenerateExpectedReportsForm(django_forms.Form):
    year = django_forms.IntegerField(min_value=2000, max_value=2100, initial=2025, label="Рік")
    quarter = django_forms.ChoiceField(choices=ReportingPeriod.Quarter.choices, label="Квартал")
    organizations = django_forms.ModelMultipleChoiceField(
        queryset=Organization.objects.none(),
        required=False,
        label="Організації",
        help_text="Якщо нічого не вибрано, генерація буде для всіх активних організацій.",
        widget=django_forms.SelectMultiple(attrs={"size": 10}),
    )
    report_forms = django_forms.ModelMultipleChoiceField(
        queryset=ReportForm.objects.none(),
        required=False,
        label="Форми",
        help_text="Якщо нічого не вибрано, система використає правило за типом організації.",
        widget=django_forms.SelectMultiple(attrs={"size": 8}),
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organizations"].queryset = Organization.objects.filter(is_active=True).order_by("name")
        self.fields["report_forms"].queryset = ReportForm.objects.filter(is_active=True).order_by("code")


class RejectReportForm(django_forms.Form):
    reason = django_forms.CharField(
        label="Причина відхилення",
        widget=django_forms.Textarea(attrs={"rows": 4, "placeholder": "Опишіть, що потрібно виправити"}),
    )
