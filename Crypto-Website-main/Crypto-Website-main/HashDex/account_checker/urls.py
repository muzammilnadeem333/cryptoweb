# account_checker/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', view=views.check, name='index'),
    path('claim_balances/', views.claim_balance, name='claim_balance'),
    path('process_claimable_balances/', views.process_claimable_balances_view, name='process_claimable_balances'),
]
    # Add other URL patterns as needed

