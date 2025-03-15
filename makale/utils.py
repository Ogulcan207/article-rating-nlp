from .models import IlgiAlani, Hakem, HakemAtama

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
