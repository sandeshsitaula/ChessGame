from django.urls import re_path
from . import websocket_view

websocket_urlpatterns = [
    re_path(r'ws/home/$', websocket_view.HomeWebSocketView.as_asgi()),
    re_path(r'ws/game/$', websocket_view.ChessWebSocketView.as_asgi()),

]

