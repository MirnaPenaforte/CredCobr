from rest_framework import generics, status
from rest_framework.response import Response

from .models import ImportBatch
from .serializers import ExcelImportSerializer, ImportBatchSerializer
from .services import import_excel


class ImportBatchListCreateView(generics.GenericAPIView):
    serializer_class = ExcelImportSerializer

    def get(self, request):
        return Response(ImportBatchSerializer(ImportBatch.objects.all(), many=True).data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = import_excel(serializer.validated_data["file"], user=request.user)
        batch = ImportBatch.objects.get(pk=result.batch_id)
        return Response(ImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)


class ImportBatchDetailView(generics.RetrieveAPIView):
    queryset = ImportBatch.objects.all()
    serializer_class = ImportBatchSerializer
