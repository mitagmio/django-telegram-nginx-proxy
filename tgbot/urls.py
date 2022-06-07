from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from dtb.settings import TELEGRAM_WEBHOOK_SECRET
from . import views

urlpatterns = [  
    # TODO: make webhook more secure
    path('', views.index, name="index"),
    path('actual-rate', views.actual_rate, name="actual_rate"),
    path(TELEGRAM_WEBHOOK_SECRET, csrf_exempt(views.TelegramBotWebhookView.as_view())), # default TELEGRAM_WEBHOOK='super_secter_webhook/'
]