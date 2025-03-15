from django.shortcuts import render, redirect
from .forms import MakaleYuklemeForm
from .models import Makale

def index(request):
    return render(request, 'makale/index.html')

def makale_yukle(request):
    if request.method == 'POST':
        form = MakaleYuklemeForm(request.POST, request.FILES)
        if form.is_valid():
            makale = form.save()
            return render(request, 'makale/yukleme_basarili.html', {'makale': makale})
    else:
        form = MakaleYuklemeForm()
    
    return render(request, 'makale/makale_yukle.html', {'form': form})
