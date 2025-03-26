from django.shortcuts import render, redirect, get_object_or_404
from .forms import MakaleYuklemeForm
from .models import Makale, AnonymizedMakale, HakemAtama, Hakem
from .utils import belirle_makale_alanlari, hakem_atama, anonymize_names_in_pdf


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

# 📌 1️⃣ Editör Paneli (Tüm makaleleri listeler)
def editor_paneli(request):
    makaleler = Makale.objects.all().order_by('-yuklenme_tarihi')  # Son yüklenen ilk görünsün
    return render(request, 'makale/editor_paneli.html', {'makaleler': makaleler})

# 📌 2️⃣ Makale Detay Sayfası
def makale_detay(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)
    anonim_makale = AnonymizedMakale.objects.filter(orijinal_makale=makale).first()
    hakem_atama = HakemAtama.objects.filter(makale=makale).first()
    
    return render(request, 'makale/makale_detay.html', {
        'makale': makale,
        'anonim_makale': anonim_makale,
        'hakem_atama': hakem_atama
    })

# 📌 3️⃣ Makale Anonimleştirme
def anonimlestir(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)

    # Girdi ve çıktı yollarını ayarla
    input_path = makale.pdf_dosya.name  # media/makaleler/...
    output_relative_path = f"anonimleştirilmiş_makaleler/anonim_{makale_id}.pdf"

    # PDF anonimleştirme işlemini yap
    anonymize_names_in_pdf(input_path, output_relative_path)

    # Modeli oluştur ya da güncelle
    anonim_makale, created = AnonymizedMakale.objects.get_or_create(
        orijinal_makale=makale,
        defaults={"anonim_makale_pdf": output_relative_path}
    )

    if not created:
        anonim_makale.anonim_makale_pdf.name = output_relative_path
        anonim_makale.save()

    return redirect('makale_detay', makale_id=makale.id)

# 📌 4️⃣ Hakem Atama İşlemi
def hakem_ata(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)
    
    # Hakem atama işlemini çağır
    secilen_hakem = hakem_atama(makale)
    
    return redirect('makale_detay', makale_id=makale.id)

# 📌 5️⃣ Makale Durum Güncelleme (Editör Makale Sürecini Değiştirebilir)
def makale_durum_guncelle(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)
    yeni_durum = request.GET.get('durum')

    if yeni_durum in ['Beklemede', 'Değerlendiriliyor', 'Tamamlandı']:
        makale.durum = yeni_durum
        makale.save()

    return redirect('makale_detay', makale_id=makale.id)