from django.db import models
from django.contrib.auth.models import AbstractUser
import hashlib
import uuid

# 🚀 Kullanıcı Modeli (Özel User Modeli)
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('yazar', 'Yazar'),
        ('editor', 'Editör'),
        ('hakem', 'Hakem'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='yazar')

    def __str__(self):
        return f"{self.username} - {self.role}"

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
    durum = models.CharField(max_length=20, choices=[
        ('Beklemede', 'Beklemede'),
        ('Değerlendiriliyor', 'Değerlendiriliyor'),
        ('Tamamlandı', 'Tamamlandı')
    ], default='Beklemede')

    def __str__(self):
        return self.baslik

# 🔒 Anonimleştirilmiş Makale Modeli
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

# 🧐 Hakem Atama Modeli
class HakemAtama(models.Model):
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE)
    hakem = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'hakem'})
    atama_tarihi = models.DateTimeField(auto_now_add=True)
    degerlendirme_yapildi = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.makale.baslik} - {self.hakem.username}"

# ✍️ Hakem Değerlendirme Modeli
class Degerlendirme(models.Model):
    hakem = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'hakem'})
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE)
    yorum = models.TextField()
    pdf_dosya = models.FileField(upload_to='degerlendirmeler/', blank=True, null=True)
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.makale.baslik} - {self.hakem.username}"

# 🕵️ İşlem Geçmişi Modeli (Sistemde Yapılan İşlemleri Takip İçin)
class Log(models.Model):
    makale = models.ForeignKey(Makale, on_delete=models.CASCADE)
    kullanici = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    islem = models.TextField()
    tarih = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tarih} - {self.kullanici.username} - {self.islem}"
