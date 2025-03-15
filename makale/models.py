from django.db import models
from django.contrib.auth.models import AbstractUser
import hashlib
import uuid

# 🚀 Kullanıcı Modeli (Hakem, Editör, Yazar Rolleri)
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('yazar', 'Yazar'),
        ('editor', 'Editör'),
        ('hakem', 'Hakem'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='yazar')

    def __str__(self):
        return f"{self.username} - {self.role}"

# 📌 İlgi Alanları Modeli (Hakemlerin ve Makalelerin Eşleşeceği Kategoriler)
class IlgiAlani(models.Model):
    KATEGORILER = [
        ('AI', 'Yapay Zeka ve Makine Öğrenimi'),
        ('HCI', 'İnsan-Bilgisayar Etkileşimi'),
        ('BIGDATA', 'Büyük Veri ve Veri Analitiği'),
        ('SECURITY', 'Siber Güvenlik'),
        ('NETWORK', 'Ağ ve Dağıtık Sistemler'),
    ]
    kategori = models.CharField(max_length=20, choices=KATEGORILER)
    isim = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.get_kategori_display()} - {self.isim}"
    
# 📌 SHA-256 ile Makale Takip Numarası Üreten Fonksiyon
def generate_tracking_id():
    unique_id = str(uuid.uuid4())
    return hashlib.sha256(unique_id.encode()).hexdigest()[:10]

# 📝 Makale Modeli
class Makale(models.Model):
    takip_numarasi = models.CharField(max_length=64, unique=True, default=generate_tracking_id)
    baslik = models.CharField(max_length=255)
    pdf_dosya = models.FileField(upload_to='makaleler/')
    yazar_email = models.EmailField()
    yuklenme_tarihi = models.DateTimeField(auto_now_add=True)
    anahtar_kelimeler = models.TextField()  # Anahtar kelimeler buraya eklenecek!
    alanlar = models.ManyToManyField(IlgiAlani, blank=True)  # Otomatik belirlenecek
    durum = models.CharField(max_length=20, choices=[
        ('Beklemede', 'Beklemede'),
        ('Değerlendiriliyor', 'Değerlendiriliyor'),
        ('Tamamlandı', 'Tamamlandı')
    ], default='Beklemede')

    def __str__(self):
        return self.baslik

# 🔒 Anonimleştirilmiş Makale Modeli (Hakemlere Gönderilecek Versiyon)
class AnonymizedMakale(models.Model):
    orijinal_makale = models.OneToOneField(Makale, on_delete=models.CASCADE)
    anonim_makale_pdf = models.FileField(upload_to='anonimleştirilmiş_makaleler/')
    islenme_tarihi = models.DateTimeField(auto_now_add=True)
    hash_degeri = models.CharField(max_length=64, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.hash_degeri:
            self.hash_degeri = hashlib.sha256(str(self.orijinal_makale.id).encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Anonimleştirilmiş: {self.orijinal_makale.baslik}"

# 📌 Hakem Modeli (Hakemlerin İlgi Alanlarını Tutuyor)
class Hakem(models.Model):
    kullanici = models.OneToOneField(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'hakem'})
    ilgi_alanlari = models.ManyToManyField(IlgiAlani, blank=True)  # Hakemlerin uzmanlık alanları

    def __str__(self):
        return f"Hakem: {self.kullanici.username}"
    
# 🧐 Hakem Atama Modeli (Hakem - Makale Eşleşmesi)
class HakemAtama(models.Model):
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE)
    hakem = models.ForeignKey(Hakem, on_delete=models.CASCADE)  # Doğrudan Hakem modeli kullanılmalı
    atama_tarihi = models.DateTimeField(auto_now_add=True)
    degerlendirme_yapildi = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.makale.baslik} - {self.hakem.kullanici.username}"

# ✍️ Hakem Değerlendirme Modeli (Hakem Yorumları)
class Degerlendirme(models.Model):
    hakem = models.ForeignKey(Hakem, on_delete=models.CASCADE)
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE)
    yorum = models.TextField()
    pdf_dosya = models.FileField(upload_to='degerlendirmeler/', blank=True, null=True)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.makale.baslik} - {self.hakem.kullanici.username}"

# 🕵️ İşlem Geçmişi Modeli (Sistemde Yapılan İşlemleri Takip İçin)
class Log(models.Model):
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE)
    kullanici = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    islem = models.TextField()
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tarih} - {self.kullanici.username} - {self.islem}"
