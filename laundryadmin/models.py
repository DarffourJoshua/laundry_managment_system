from django.db import models

# Create your models here.
class CompanySettings(models.Model):
    """
        Singleton model - only one row should ever exist
        Represents the laundry business's own profile
    """

    company_name = models.CharField(max_length=50)
    company_email = models.EmailField()
    email_password = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company/logo', blank=True, null=True)
    fav_icon        = models.ImageField(upload_to='company/favicon/', blank=True, null=True)
    phone           = models.CharField(max_length=20, blank=True)
    address         = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Company Settings'

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        # Enforce singleton - only one company record allowed
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    
class Service(models.Model):
    """
    Laundry services the company offers e.g. Wash & Fold, Dry Clean.
    """

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name