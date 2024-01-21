from django.urls import re_path

from app_dir import consumers

websocket_urlpatterns = [
    re_path(r"ws/main-page/(?P<coin_name>\w+)/$", consumers.ClientConsumer.as_asgi()),
    re_path(r"ws/account/$", consumers.AccountConsumer.as_asgi()),
]
