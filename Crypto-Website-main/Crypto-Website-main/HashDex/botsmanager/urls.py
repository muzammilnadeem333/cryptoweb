from django.urls import path
from . import views

urlpatterns = [
   path('', view=views.run_bot, name='bot_interface'),
   path('handler/', view=views.handler, name='handler'),
   path('get_running_bots/', view=views.get_running_bots, name='GET RUNNING BOTS'),
   path('view_logs/<uuid:bot_uuid>/', views.view_logs, name='view_logs'),
   path('stop_bot/', views.stop_bot, name='stop_bot'),
   path('start_bot/', views.start_bot, name='start_bot'),
   path('remove_bot/', views.delete_bot, name='remove_bot'),
   path('fetch-paths/', views.fetch_paths, name='fetch_paths'),
   path('clone/', views.render_clone, name='clone'),
   path('clone_bot/', views.clone_bot, name='clone_bot'),
   path('multi_transaction_bot/', views.multi_transaction_bot_interface_view, name='multi_transaction_bot_interface'),
   path('multi_transaction_bot/handler2/', view=views.handler_multi_transaction_bots, name='handler2'),
   path('multi_operational_running_bots/', view=views.multi_get_running_bots, name='Multi Operational Running Bots'),
   path('multi_view_logs/<uuid:bot_uuid>/', views.multi_view_logs, name='view_logs2'),
   path('start_bot2/', views.multi_start_bot, name='start_bot2'),
   path('stop_bot2/', views.multi_stop_bot, name='stop_bot2'),
   path('remove_bot2/', views.multi_delete_bot, name='remove_bot2'),
   path('clone_bot2/', views.multi_clone_bot, name='clone_bot2'),
   path('clone2/', views.render_clone_multi, name='clone2'),
]