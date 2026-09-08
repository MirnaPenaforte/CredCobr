from django.urls import path

from .views import customer_receivables_detail, home, receivable_detail, receivable_list, report_download, report_list, report_pdf, state_dashboard


urlpatterns = [
    path("", home, name="home"),
    path("states/<str:code>/", state_dashboard, name="state-dashboard"),
    path("receivables/", receivable_list, name="receivable-list"),
    path("receivables/customers/<int:pk>/", customer_receivables_detail, name="customer-receivables-detail"),
    path("receivables/<int:pk>/", receivable_detail, name="receivable-detail"),
    path("reports/", report_list, name="report-list"),
    path("reports/<int:pk>/download/", report_download, name="report-download"),
    path("reports/<int:pk>/pdf/", report_pdf, name="report-pdf"),
]
