from django.db import models
from django.contrib.auth.models import AbstractUser
import hashlib
import os

# Kullanıcı Modeli
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

# Belge Modeli
class Document(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

# Anonimleştirilmiş Belge Modeli
class AnonymizedDocument(models.Model):
    original_document = models.OneToOneField(Document, on_delete=models.CASCADE)
    anonymized_file = models.FileField(upload_to='anonymized_documents/')
    processed_at = models.DateTimeField(auto_now_add=True)
    hash_value = models.CharField(max_length=64, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.hash_value:
            self.hash_value = hashlib.sha256(str(self.original_document.id).encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Anonimleştirilmiş: {self.original_document.title}"

# İşlem Geçmişi Modeli
class ProcessingHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    anonymized_document = models.ForeignKey(AnonymizedDocument, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    operation = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user.email} - {self.operation} - {self.timestamp}"
