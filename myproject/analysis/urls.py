from django.urls import path
from . import views
from .views import debug_template_dirs

urlpatterns = [
    path('', views.upload_csv, name='upload_csv'),
     path('debug-templates/', debug_template_dirs, name='debug_templates'),
]