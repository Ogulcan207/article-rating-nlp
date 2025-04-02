from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='index'),  # Ana sayfa
    path('makale-yukle/', views.makale_yukle, name='makale_yukle'),
    path('editor/', views.editor_paneli, name='editor_paneli'),
    path('makale-sorgula/', views.makale_sorgula, name='makale_sorgula'),
    path('makale-sorgula/sorgu-detay/', views.makale_sorgu_detay, name='makale_sorgu_detay'),
    path('makale-sorgula/<int:makale_id>/duzenle/', views.makale_duzenle, name='makale_duzenle'),
    path('makale/<int:makale_id>/mesajlar/', views.makale_mesajlar, {'rol': 'yazar'}, name='makale_mesajlar'),
    path('editor/makale/<int:makale_id>/mesajlar/', views.makale_mesajlar, {'rol': 'editor'}, name='editor_makale_mesajlar'),
    path('editor/makale/<int:makale_id>/', views.makale_detay, name='makale_detay'),
    path('editor/makale/<int:makale_id>/anonimlestir/', views.anonimlestir, name='anonimlestir'),
    path('editor/makale/<int:makale_id>/hakem-ata/', views.hakem_ata, name='hakem_ata'),
    path('editor/makale/<int:makale_id>/durum-guncelle/', views.makale_durum_guncelle, name='makale_durum_guncelle'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)