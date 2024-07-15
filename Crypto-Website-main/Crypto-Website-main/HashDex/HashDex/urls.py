from django.contrib import admin
from django.urls import path , include
from HashDex import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', view=views.index_login, name='login - Prove Your Identity'),
    path('accounts/login/', view=views.index_login, name='login - Prove Your Identity'),
    path('accounts/login/dashboard/', view=views.dashboard , name='Dashboard'),
    path('dashboard/', view=views.dashboard , name='Dashboard'),
    path('account_checker/', include('account_checker.urls')),
    path('run_bot/', include('botsmanager.urls')),
    path('liquidity/', include('liquiditypool.urls')),
    path('offers/', include('trader.urls')),
]
