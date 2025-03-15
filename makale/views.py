from django.shortcuts import render, redirect
from .forms import MakaleYuklemeForm
from .models import Makale
from .utils import belirle_makale_alanlari, hakem_atama


def index(request):
    return render(request, 'makale/index.html')

def makale_yukle(request):
    if request.method == 'POST':
        form = MakaleYuklemeForm(request.POST, request.FILES)
        if form.is_valid():
            makale = form.save()
            
            # Makale alanlarını belirle
            makale.alanlar.set(belirle_makale_alanlari(makale.anahtar_kelimeler))
            makale.save()

            # Hakem ata
            atanan_hakem = hakem_atama(makale)

            return render(request, 'makale/yukleme_basarili.html', {'makale': makale, 'hakem': atanan_hakem})
    else:
        form = MakaleYuklemeForm()
    
    return render(request, 'makale/makale_yukle.html', {'form': form})
