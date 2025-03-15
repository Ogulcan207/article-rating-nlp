from django.contrib import admin
from django.urls import path, include  # include fonksiyonunu import ettik

urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin paneli
    path('', include('makale.urls')),  # makale uygulamasının URL'lerini dahil ettik
]
