from django.urls import path

from . import views
# from . import consumers

urlpatterns = [
    path('health', views.healthcheck_view),
    path('calc', views.calculate_view)
]

# websocket_urlpatterns = [
#     path("ws/sync", consumers.SyncConsumer.as_asgi()),
# ]