from datetime import date

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import can_access_all_states, filter_by_state_scope

from .models import ReportExecution
from .serializers import ReportExecutionSerializer
from .services import generate_all_reports
from shared.dates import parse_date


def scoped_reports(request):
    queryset = ReportExecution.objects.select_related("state")
    if can_access_all_states(request.user):
        return queryset
    allowed = request.user.authorized_states.all()
    return queryset.filter(state__in=allowed)


class ReportListView(generics.ListAPIView):
    serializer_class = ReportExecutionSerializer

    def get_queryset(self):
        return scoped_reports(self.request)


class ReportDetailView(generics.RetrieveAPIView):
    serializer_class = ReportExecutionSerializer

    def get_queryset(self):
        return scoped_reports(self.request)


class ReportGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser and request.user.role not in {"administrator", "manager"}:
            return Response({"detail": "Permissão insuficiente."}, status=status.HTTP_403_FORBIDDEN)
        raw_date = request.data.get("date")
        target_date = parse_date(raw_date) if raw_date else date.today()
        state = request.data.get("state")
        executions = generate_all_reports(
            reference_date=target_date,
            states=[state.upper()] if state else None,
            include_pdf=bool(request.data.get("pdf", False)),
        )
        return Response(ReportExecutionSerializer(executions, many=True, context={"request": request}).data, status=status.HTTP_201_CREATED)
