from asgiref.sync import sync_to_async

from main_app.models import CalculatedResult
from main_app.serializers import CalculatedResultSerializer

async def get_result_history():
    async_get_data = sync_to_async(lambda: 
        CalculatedResultSerializer(
            CalculatedResult.objects.all(), # returns new queryset so non-blocking
            many=True
        ).data
    )
    
    return await async_get_data() # await coroutine