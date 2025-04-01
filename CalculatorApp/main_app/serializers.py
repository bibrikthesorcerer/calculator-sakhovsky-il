from rest_framework.serializers import ModelSerializer

from main_app.models import CalculatedResult


class CalculatedResultSerializer(ModelSerializer):
    class Meta:
        model=CalculatedResult
        fields=['id','expression','result','timestamp']