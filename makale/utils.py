from .models import IlgiAlani, Hakem, HakemAtama
import fitz, os, spacy
from django.conf import settings
import re
from collections import Counter
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

nlp = spacy.load("en_core_web_trf")  # Daha güçlü bir NLP modeli
AES_KEY = b'16byteslongkey!!'

def pad(text):
    return text + (16 - len(text) % 16) * chr(16 - len(text) % 16)

def unpad(text):
    return text[:-ord(text[-1])]

def encrypt_text_aes(plain_text):
    cipher = AES.new(AES_KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(plain_text).encode('utf-8'))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return f"{iv}:{ct}"  # IV'yi ayırıyoruz

def decrypt_text_aes(encrypted_text):
    iv, ct = encrypted_text.split(":")
    iv = base64.b64decode(iv)
    ct = base64.b64decode(ct)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct).decode('utf-8'))

def belirle_makale_alanlari_nlp(text):
    keywords = extract_keywords_with_nlp(text)

    ilgi_alani_etiketleri = {
        'AI': ['deep learning', 'machine', 'neural', 'nlp', 'algorithm', 'recognition', 'ai', 'cnn', 'lstm', 'svm', 'transformer', 'bert', 'model'],
        'HCI': ['user', 'emotion', 'interface', 'stress', 'arousal', 'reaction', 'signal', 'eeg', 'experiment'],
        'BIGDATA': ['data', 'analysis', 'dataset', 'visualization', 'streaming', 'bigdata', 'feature', 'dimensionality'],
        'SECURITY': ['security', 'blockchain', 'encryption', 'attack', 'cyber', 'authentication'],
        'NETWORK': ['network', 'protocol', 'communication', '5g', 'iot']
    }

    sayac = {alan: 0 for alan in ilgi_alani_etiketleri}

    for alan, kelime_listesi in ilgi_alani_etiketleri.items():
        for kelime in kelime_listesi:
            if any(kelime in k for k in keywords):
                sayac[alan] += 1

    en_yuksek = max(sayac.values())
    if en_yuksek == 0:
        return []

    # 📌 SADECE en yüksek eşleşen 1 tane alanı dön
    en_uygun_alan = max(sayac, key=sayac.get)
    return IlgiAlani.objects.filter(kategori=en_uygun_alan)


def extract_text_from_pdf(pdf_path):
    full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
    doc = fitz.open(full_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    doc.close()
    return text

def extract_keywords_with_nlp(text, max_keywords=30):
    doc = nlp(text)
    keywords = []

    for token in doc:
        if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop and len(token.text) > 2:
            keywords.append(token.lemma_.lower())

    # En sık geçen max_keywords kelimeyi al
    most_common = Counter(keywords).most_common(max_keywords)
    return [word for word, freq in most_common]


def hakem_atama(makale):
    uygun_hakemler = Hakem.objects.filter(ilgi_alanlari__in=makale.alanlar.all()).distinct()

    if uygun_hakemler.exists():
        en_uygun_hakem = uygun_hakemler.order_by('?').first()  # Rastgele uygun hakemi seç
        HakemAtama.objects.create(makale=makale, hakem=en_uygun_hakem)
        return en_uygun_hakem.kullanici.username
    return None

def anonymize_names_in_pdf(input_pdf_path, output_relative_path, encrypted_names_dict):

    input_path = os.path.join(settings.MEDIA_ROOT, input_pdf_path)
    output_path = os.path.join(settings.MEDIA_ROOT, output_relative_path)
    doc = fitz.open(input_path)

    # Başlık ve yapı tanımları
    skip_sections = ["introduction", "related work", "acknowledgement", "teşekkür"]
    stop_at_reference = ["references", "kaynakça"]
    in_skipped_section = False
    in_references = False
    reference_done = False

    for page in doc:
        blocks = page.get_text("blocks")
        sorted_blocks = sorted(blocks, key=lambda b: (b[1], b[0]))  # top to bottom

        for block in sorted_blocks:
            text = block[4].strip()
            lowered = text.lower()

            # REFERANS kontrolü
            if any(heading in lowered for heading in stop_at_reference):
                in_references = True
                continue

            if in_references:
                if re.match(r"^\[\d+\]", text):
                    continue  # referans satırı
                elif len(text.split()) > 10:
                    reference_done = True

            # ATLA: referanslar veya özel bölümler
            if any(section in lowered for section in skip_sections):
                in_skipped_section = True
                continue

            if in_skipped_section and not reference_done:
                continue

            if not text:
                continue

            # NLP ile kişi, kurum vb. bul
            nlp_doc = nlp(text)
            for ent in nlp_doc.ents:
                if ent.label_ in ["PERSON", "ORG", "EMAIL", "GPE", "LOC"]:
                    entity_text = ent.text.strip()
                    if not entity_text:
                        continue

                    if ent.label_ == "ORG" and not any(x in entity_text.lower() for x in ["university", "institute", "faculty", "department"]):
                        continue

                    encrypted = encrypt_text_aes(entity_text)
                    encrypted_names_dict[entity_text] = encrypted

                    for occ in page.search_for(entity_text):
                        page.draw_rect(occ, color=(1, 1, 1), fill=(1, 1, 1))

            # Regex destekli gizleme
            regex_patterns = [
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                r"(university|institute|faculty|department) of [\w\s]+",
                r"\baddress[:\- ]?.*", r"\bemail[:\- ]?.*", r"\bphone[:\- ]?.*"
            ]
            for pattern in regex_patterns:
                for match in re.findall(pattern, text, flags=re.IGNORECASE):
                    match = match.strip()
                    if match in encrypted_names_dict:
                        continue

                    encrypted = encrypt_text_aes(match)
                    encrypted_names_dict[match] = encrypted

                    for occ in page.search_for(match):
                        page.draw_rect(occ, color=(1, 1, 1), fill=(1, 1, 1))

    doc.save(output_path)
    doc.close()
    return output_relative_path
