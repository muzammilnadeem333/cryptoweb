from django.urls import path
from . import views

urlpatterns = [
   path('', view=views.liquidity_pool_render, name='liquidity_pool'),
   path('result/', view=views.get_liquidity_pool, name='get_res'),
   path('deposit/', view=views.deposit_interface, name='deposit'),
   path('withdraw/', view=views.withdraw, name='withdraw'),
   path('deposit_liquidity_pool/', view=views.establish_trustline_and_deposit, name='deposit_liquidity_pool'),
   path('withdraw_liquidity_pool/', view=views.withdraw_from_liquidity_pool, name='withdraw_liquidity_pool'),
   path('calculateID/', view=views.calculate_id, name='calculate_id'),
   path('calculate_liquidity_pool_id/', view=views.calculate_liquidity_pool_id_view, name='calculate_liquidity_pool'),
   path('establish_pool_share/', view=views.establish_pool_share_trust, name='Pool Share'),
   path('establish_pool_share_trust/', view=views.establish_pool_share_trust_view, name='establish_pool_trust'),

]