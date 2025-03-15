from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Ana sayfa
    path('makale-yukle/', views.makale_yukle, name='makale_yukle'),
]
