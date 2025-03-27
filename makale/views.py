from django.shortcuts import render, redirect, get_object_or_404
from .forms import MakaleYuklemeForm
from .models import Makale, AnonymizedMakale, HakemAtama, Hakem
from .utils import belirle_makale_alanlari_nlp, hakem_atama, anonymize_names_in_pdf, extract_keywords_with_nlp, extract_text_from_pdf
from django.core.files.base import ContentFile
import os

def index(request):
    return render(request, 'makale/index.html')


def makale_yukle(request):
    if request.method == 'POST':
        form = MakaleYuklemeForm(request.POST, request.FILES)
        if form.is_valid():
            makale = form.save(commit=False)
            uploaded_file = request.FILES['pdf_dosya']
            makale.save()

            extension = uploaded_file.name.split('.')[-1]
            new_filename = f"makale_{makale.id}_{makale.baslik.replace(' ', '_')}.{extension}"
            makale.pdf_dosya.save(new_filename, uploaded_file, save=True)

            text = extract_text_from_pdf(makale.pdf_dosya.name)

            keywords = extract_keywords_with_nlp(text)
            makale.anahtar_kelimeler = ", ".join(keywords)

            alanlar = belirle_makale_alanlari_nlp(text)
            makale.alanlar.set(alanlar)

            makale.save()

            return render(request, 'makale/yukleme_basarili.html', {'makale': makale})
    else:
        form = MakaleYuklemeForm()

    return render(request, 'makale/makale_yukle.html', {'form': form})


def editor_paneli(request):
    makaleler = Makale.objects.all().order_by('-yuklenme_tarihi')  # Son yüklenen ilk görünsün
    return render(request, 'makale/editor_paneli.html', {'makaleler': makaleler})

def makale_detay(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)
    anonim_makale = AnonymizedMakale.objects.filter(orijinal_makale=makale).first()
    hakem_atama = HakemAtama.objects.filter(makale=makale).first()
    
    return render(request, 'makale/makale_detay.html', {
        'makale': makale,
        'anonim_makale': anonim_makale,
        'hakem_atama': hakem_atama
    })

def anonimlestir(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)

    input_path = makale.pdf_dosya.name  # Örnek: makaleler/makale_1_bla.pdf
    output_relative_path = f"anonim_makaleler/anonim_{makale.id}_{makale.baslik.replace(' ', '_')}.pdf"

    encrypted_names_dict = {}

    # 📌 Güncellenmiş anonimleştirme fonksiyonu çağrılır
    anonymize_names_in_pdf(input_path, output_relative_path, encrypted_names_dict)

    # 📦 Anonimleştirilmiş makale modeline kaydedilir
    anonim_makale, created = AnonymizedMakale.objects.get_or_create(
        orijinal_makale=makale,
        defaults={
            "anonim_makale_pdf": output_relative_path,
            "sifreli_veriler": encrypted_names_dict
        }
    )

    # ❗ Eğer zaten varsa güncelle
    if not created:
        anonim_makale.anonim_makale_pdf.name = output_relative_path
        anonim_makale.sifreli_veriler = encrypted_names_dict
        anonim_makale.save()

    return redirect('makale_detay', makale_id=makale.id)


def hakem_ata(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)
    
    # Hakem atama işlemini çağır
    secilen_hakem = hakem_atama(makale)
    
    return redirect('makale_detay', makale_id=makale.id)

def makale_durum_guncelle(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)
    yeni_durum = request.GET.get('durum')

    if yeni_durum in ['Beklemede', 'Değerlendiriliyor', 'Tamamlandı']:
        makale.durum = yeni_durum
        makale.save()

    return redirect('makale_detay', makale_id=makale.id)