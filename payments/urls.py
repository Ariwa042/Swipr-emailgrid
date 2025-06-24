from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('plans/', views.subscription_plans, name='subscription_plans'),
    path('checkout/<int:plan_id>/', views.payment, name='checkout'),
    path('payment/<int:plan_id>/', views.payment, name='payment'),
    path('payment-instructions/<str:payment_id>/', views.payment_instructions, name='payment_instructions'),
    path('check-status/<str:payment_id>/', views.check_payment_status, name='check_payment_status'),
]