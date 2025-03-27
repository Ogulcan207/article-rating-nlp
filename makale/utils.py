from .models import IlgiAlani, Hakem, HakemAtama
import fitz, os, spacy
from django.conf import settings
import re

nlp = spacy.load("en_core_web_trf")  # Daha güçlü bir NLP modeli


def belirle_makale_alanlari_nlp(text):
    keywords = extract_keywords_with_nlp(text)

    ilgi_alani_etiketleri = {
        'AI': ['deep learning', 'machine', 'neural', 'nlp', 'algorithm', 'recognition', 'ai', 'cnn', 'lstm', 'svm', 'classification', 'transformer', 'bert', 'model'],
        'HCI': ['user', 'emotion', 'interface', 'stress', 'arousal', 'reaction', 'signal', 'eeg', 'experiment'],
        'BIGDATA': ['data', 'analysis', 'dataset', 'visualization', 'streaming', 'bigdata', 'feature', 'dimensionality'],
        'SECURITY': ['security', 'blockchain', 'encryption', 'attack', 'cyber', 'authentication'],
        'NETWORK': ['network', 'protocol', 'communication', '5g', 'iot']
    }

    sayac = {alan: 0 for alan in ilgi_alani_etiketleri}

    for alan, kelime_listesi in ilgi_alani_etiketleri.items():
        for kelime in kelime_listesi:
            if any(kelime in k for k in keywords):  # keyword içinde geçiyorsa
                sayac[alan] += 1

    en_yuksek = max(sayac.values())
    if en_yuksek == 0:
        return []

    en_uygun_alanlar = [alan for alan, skor in sayac.items() if skor == en_yuksek]
    return IlgiAlani.objects.filter(kategori__in=en_uygun_alanlar)



def extract_text_from_pdf(pdf_path):
    full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
    doc = fitz.open(full_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    doc.close()
    return text

def extract_keywords_with_nlp(text):
    doc = nlp(text)
    keywords = set()
    for token in doc:
        if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop and len(token.text) > 2:
            keywords.add(token.lemma_.lower())
    return list(keywords)

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