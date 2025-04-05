import re
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed, HttpResponseServerError, HttpResponseBadRequest

from .utils import validate_request
from .runner import CalcManager
from .models import CalculatedResult
from .serializers import CalculatedResultSerializer

async def healthcheck_view(request):
    if request.method != "GET":
        return HttpResponseNotAllowed()
    return HttpResponse()

async def calculate_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed()
    try:
        float_mode, body = await validate_request(request)        
    except Exception as e:        
        print(e)
        return HttpResponseBadRequest(e)
    # perform calculations
    try:
        runner = CalcManager(
            float_mode=float_mode,
            input_data=body
        )
        result = runner.run_app() # got to be async too
        # log result if everything is ok
        body = re.sub(r"\s", "", body)
        res_obj = await CalculatedResult.objects.acreate(
            expression=body,
            result=result,
            # auto timestamp
        )
        data = CalculatedResultSerializer(res_obj).data
        return JsonResponse(data)
    except Exception as e:
        print(e)
        return HttpResponseServerError("Runtime error occured")
    

