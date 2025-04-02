from django.shortcuts import render, redirect, get_object_or_404
from .forms import MakaleYuklemeForm, MakaleForm, MakaleMesajForm
from .models import Makale, AnonymizedMakale, HakemAtama, Hakem, Log
from .utils import belirle_makale_alanlari_nlp, hakem_atama, anonymize_names_in_pdf, extract_keywords_with_nlp, extract_text_from_pdf
from django.urls import reverse
from django.utils.timezone import now


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

            Log.objects.create(
                makale=makale,
                kullanici=request.user if request.user.is_authenticated else None,
                islem=f"Makale Yükledi: {makale.baslik}",
                tarih=now()
            )

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

    # POST ile bilgi türü güncellenirse
    if request.method == 'POST' and 'bilgi_turleri' in request.POST:
        selected = request.POST.getlist('bilgi_turleri')
        if anonim_makale:
            anonim_makale.secilen_bilgi_turleri = selected
            anonim_makale.save()

    return render(request, 'makale/makale_detay.html', {
        'makale': makale,
        'anonim_makale': anonim_makale,
        'hakem_atama': hakem_atama
    })


def anonimlestir(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)

    input_path = makale.pdf_dosya.name
    output_relative_path = f"anonim_makaleler/anonim_{makale.id}_{makale.baslik.replace(' ', '_')}.pdf"
    encrypted_names_dict = {}

    # 🔄 Editörün seçtiği bilgi türlerini al
    secilen_turler = request.POST.getlist("bilgi_turleri")
    if not secilen_turler:
        secilen_turler = ["PERSON", "ORG", "EMAIL", "GPE", "LOC", "IMAGE"]  # Default

    anonymize_names_in_pdf(
        input_path,
        output_relative_path,
        encrypted_names_dict,
        secilen_turler,
        makale.id
    )

    anonim_makale, created = AnonymizedMakale.objects.get_or_create(
        orijinal_makale=makale,
        defaults={
            "anonim_makale_pdf": output_relative_path,
            "sifreli_veriler": encrypted_names_dict,
            "secilen_bilgi_turleri": secilen_turler
        }
    )

    if not created:
        anonim_makale.anonim_makale_pdf.name = output_relative_path
        anonim_makale.sifreli_veriler = encrypted_names_dict
        anonim_makale.secilen_bilgi_turleri = secilen_turler
        anonim_makale.save()

    Log.objects.create(
        makale=makale,
        kullanici=request.user if request.user.is_authenticated else None,  # Kullanıcı oturum açmışsa kaydet
        islem=f"Makale Anonimleştirildi: {makale.baslik}",
        tarih=now()
    )

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

    Log.objects.create(
        makale=makale,
        kullanici=request.user if request.user.is_authenticated else None,  # Kullanıcı oturum açmışsa kaydet
        islem=f"Makale Durumu Güncellendi: {makale.baslik}",
        tarih=now()
    )

    return redirect('makale_detay', makale_id=makale.id)

def makale_sorgula(request):
    return render(request, 'makale/makale_sorgula.html')

def makale_sorgu_detay(request):
    sorgu_no = request.GET.get('sorgu_no', '')  # URL'den sorgu numarasını al
    makale = Makale.objects.filter(takip_numarasi=sorgu_no).first()  # Takip numarasına göre makale bul

    if not makale:
        return render(request, 'makale/makale_sorgu_detay.html', {'error': 'Makale bulunamadı.'})
    
    Log.objects.create(
        makale=makale,
        kullanici=request.user if request.user.is_authenticated else None,  # Kullanıcı oturum açmışsa kaydet
        islem=f"Makale Sorgulandı: {makale.baslik}",
        tarih=now()
    )

    return render(request, 'makale/makale_sorgu_detay.html', {'makale': makale})

def makale_duzenle(request, makale_id):
    makale = get_object_or_404(Makale, id=makale_id)  # Makale bulunamazsa 404 hatası ver

    if request.method == "POST":
        form = MakaleForm(request.POST, request.FILES, instance=makale)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('makale_sorgu_detay')}?sorgu_no={makale.takip_numarasi}")  # Güncelleme sonrası yönlendirme

    else:
        form = MakaleForm(instance=makale)  # Mevcut makale bilgileri formda görünsün

    Log.objects.create(
        makale=makale,
        kullanici=request.user if request.user.is_authenticated else None,  # Kullanıcı oturum açmışsa kaydet
        islem=f"Makale Düzenlendi: {makale.baslik}",
        tarih=now()
    )

    return render(request, 'makale/makale_duzenle.html', {'form': form, 'makale': makale})

def makale_mesajlar(request, makale_id, rol):
    makale = get_object_or_404(Makale, id=makale_id)
    mesajlar = makale.mesajlar.order_by('tarih')  # Mesajları tarihe göre sırala
    form = MakaleMesajForm()

    if request.method == "POST":
        form = MakaleMesajForm(request.POST)
        if form.is_valid():
            mesaj = form.save(commit=False)  # Formdan mesaj objesi oluştur
            mesaj.makale = makale  # Mesajı ilgili makaleye bağla

            # Yazar mı editör mü belirle
            if rol == "yazar":
                mesaj.gonderen = 'Yazar'
            elif rol == "editor":
                mesaj.gonderen = 'Editör'
            else:
                return redirect('makale_mesajlar', makale_id=makale.id)  # Geçersiz rol varsa yönlendir

            mesaj.save()  # Mesajı veritabanına kaydet

            Log.objects.create(
                makale=makale,
                kullanici=request.user if request.user.is_authenticated else None,  # Kullanıcı oturum açmışsa kaydet
                islem=f"{mesaj.gonderen} tarafından yeni bir mesaj gönderildi: {mesaj.icerik}",
                tarih=now()
            )

            # Doğru URL'ye yönlendir
            if rol == "yazar":
                return redirect('makale_mesajlar', makale_id=makale.id)
            elif rol == "editor":
                return redirect('editor_makale_mesajlar', makale_id=makale.id)

    return render(request, 'makale/makale_mesajlar.html', {
        'makale': makale,
        'mesajlar': mesajlar,
        'form': form,
        'rol': rol  # HTML tarafında da rolü göstermek için
    })