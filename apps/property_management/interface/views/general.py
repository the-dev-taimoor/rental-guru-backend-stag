from rest_framework import status, viewsets

from common.utils import CustomResponse


class GeneralViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return CustomResponse({'data': response.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return CustomResponse({'data': response.data}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return CustomResponse({'data': response.data}, status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return CustomResponse({'data': response.data}, status=status.HTTP_200_OK)
