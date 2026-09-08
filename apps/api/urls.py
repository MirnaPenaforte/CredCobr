from django.urls import include, path

from apps.dashboard.api import DashboardSummaryView, DashboardTopCustomersView, DashboardTopGroupsView
from apps.reports.api import ReportDetailView, ReportGenerateView, ReportListView


urlpatterns = [
    path("imports/", include("apps.imports.urls")),
    path("receivables/", include("apps.receivables.urls")),
    path("collections/", include("apps.collections.urls")),
    path("reports/", ReportListView.as_view()),
    path("reports/generate/", ReportGenerateView.as_view()),
    path("reports/<int:pk>/", ReportDetailView.as_view()),
    path("dashboards/summary/", DashboardSummaryView.as_view()),
    path("dashboards/top-groups/", DashboardTopGroupsView.as_view()),
    path("dashboards/top-customers/", DashboardTopCustomersView.as_view()),
]
