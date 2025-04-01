import json
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed, HttpResponseServerError

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
    float_mode = request.GET.get('float', 'false')
    float_mode = True if float_mode == "true" else False
    body = json.loads(request.body.decode('utf-8'))
    # perform calculations
    try:
        runner = CalcManager(
            float_mode=float_mode,
            input_data=body
        )
        result = runner.run_app() # got to be async too
        # log result if everything is ok
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