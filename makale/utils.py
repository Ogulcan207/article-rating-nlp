from .models import IlgiAlani, Hakem, HakemAtama
import fitz, os, spacy
from django.conf import settings

# 📌 Anahtar kelimelerden makale alanlarını belirleme fonksiyonu
def belirle_makale_alanlari(anahtar_kelimeler):
    alanlar = []
    keywordler_lower = anahtar_kelimeler.lower().split(", ")

    ilgi_alanlari = {
        'AI': ['derin öğrenme', 'makine öğrenimi', 'doğal dil işleme', 'bilgisayarla görü', 'generatif yapay zeka'],
        'HCI': ['beyin-bilgisayar arayüzü', 'kullanıcı deneyimi', 'artırılmış gerçeklik', 'sanallık'],
        'BIGDATA': ['veri madenciliği', 'veri görselleştirme', 'hadoop', 'spark', 'zaman serisi analizi'],
        'SECURITY': ['şifreleme', 'güvenli yazılım', 'ağ güvenliği', 'kimlik doğrulama', 'adli bilişim'],
        'NETWORK': ['5g', 'bulut bilişim', 'blockchain', 'p2p', 'merkeziyetsiz sistemler']
    }

    for kategori, kelimeler in ilgi_alanlari.items():
        for kelime in kelimeler:
            if any(k in kelime for k in keywordler_lower):
                ilgi_alani = IlgiAlani.objects.filter(kategori=kategori, isim=kelime).first()
                if ilgi_alani and ilgi_alani not in alanlar:
                    alanlar.append(ilgi_alani)

    return alanlar

# 📌 Hakem atama fonksiyonu
def hakem_atama(makale):
    uygun_hakemler = Hakem.objects.filter(ilgi_alanlari__in=makale.alanlar.all()).distinct()

    if uygun_hakemler.exists():
        en_uygun_hakem = uygun_hakemler.order_by('?').first()  # Rastgele uygun hakemi seç
        HakemAtama.objects.create(makale=makale, hakem=en_uygun_hakem)
        return en_uygun_hakem.kullanici.username
    return None

nlp = spacy.load("en_core_web_trf")  # Daha güçlü bir model, yüklenmiş olmalı

def anonymize_names_in_pdf(input_pdf_path, output_relative_path):
    """
    Belirtilen PDF dosyasındaki kişi isimlerini beyaz kutu ile kapatır ve
    anonimleştirilmiş dosyayı belirtilen konuma kaydeder.
    """

    input_path = os.path.join(settings.MEDIA_ROOT, input_pdf_path)
    output_path = os.path.join(settings.MEDIA_ROOT, output_relative_path)

    doc = fitz.open(input_path)

    for page in doc:
        text = page.get_text("text")
        nlp_doc = nlp(text)

        for ent in nlp_doc.ents:
            if ent.label_ == "PERSON" and ent.text.strip():
                for occ in page.search_for(ent.text):
                    page.draw_rect(occ, color=(1, 1, 1), fill=(1, 1, 1))  # Beyaz dikdörtgen

    doc.save(output_path)
    doc.close()

    return output_relative_path