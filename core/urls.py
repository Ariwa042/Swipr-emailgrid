from django.urls import path
from . import views
from . import endpoint

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/create/', views.create_campaign, name='create_campaign'),
    path('campaigns/<str:pk>/', views.campaign_detail, name='campaign_detail'),
    path('webhook/<str:campaign_id>/', endpoint.webhook_victim_info, name='webhook_victim_info'),
    path('tracking/pixel/<str:campaign_id>/', views.tracking_pixel, name='tracking_pixel'),
    path('victims/', views.view_victim_info, name='victim_info_list'),
]
