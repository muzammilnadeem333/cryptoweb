from django.urls import path
from . import views

urlpatterns = [
   path('manage_sell_offers', view=views.render_sell_offer, name='sell_offer_interface'),
   path('manage_sell_offers_create', view=views.create_sell_offer, name='sell_offer'),
   path('manage_buy_offers_create', view=views.create_buy_offer, name='buy_offer'),
   path('manage_buy_offers', view=views.render_buy_offer, name='buy_offer_interface'),

]