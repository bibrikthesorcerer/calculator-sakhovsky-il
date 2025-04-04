import json
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

async def validate_request(request):
    #float-mode validation
    float_mode = request.GET.get('float', 'false')
    if float_mode not in ['false','true']:
        raise Exception("Incorrect float value")
    float_mode = True if float_mode == "true" else False

    #request data validation
    if not request.body:
        raise Exception("Empty request body")
    body = json.loads(request.body.decode('utf-8'))
    if not isinstance(body, str):
        raise Exception("Incorrect input data ", input=body)
    return (float_mode, body)
    