from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/scan/(?P<channel_uuid>[\w-]+)/$', consumers.ScanConsumer.as_asgi()),
]
