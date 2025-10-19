from django.db import models
from django.utils import timezone

class ToolCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Asbob kategoriyasi"
        verbose_name_plural = "Asbob kategoriyalari"

class Tool(models.Model):
    name = models.CharField(max_length=200, verbose_name="Asbob nomi")
    category = models.ForeignKey(ToolCategory, on_delete=models.CASCADE, verbose_name="Kategoriya")
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kunlik narx")
    quantity_total = models.IntegerField(verbose_name="Jami soni")
    quantity_available = models.IntegerField(verbose_name="Mavjud soni")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Yangi obyekt
            self.quantity_available = self.quantity_total
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.quantity_available}/{self.quantity_total})"
    
    class Meta:
        verbose_name = "Asbob"
        verbose_name_plural = "Asboblar"

class Customer(models.Model):
    name = models.CharField(max_length=200, verbose_name="Ism")
    phone = models.CharField(max_length=20, verbose_name="Telefon")
    address = models.TextField(verbose_name="Manzil")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Mijoz"
        verbose_name_plural = "Mijozlar"

class Rental(models.Model):
    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('completed', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Mijoz")
    start_date = models.DateField(verbose_name="Boshlanish sanasi", default=timezone.now)
    end_date = models.DateField(null=True, blank=True, verbose_name="Tugash sanasi")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Jami summa")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Holati")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_total_days(self):
        if self.end_date:
            return (self.end_date - self.start_date).days + 1
        else:
            return (timezone.now().date() - self.start_date).days + 1
    
    def calculate_total(self):
        items = self.rentalitem_set.all()
        total = sum(item.total_amount for item in items)
        self.total_amount = total
        self.save()
        return total
    
    def __str__(self):
        return f"{self.customer.name} - {self.start_date}"
    
    class Meta:
        verbose_name = "Ijara"
        verbose_name_plural = "Ijaralar"

class RentalItem(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, verbose_name="Asbob")
    quantity = models.IntegerField(verbose_name="Soni")
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kunlik narx")
    
    @property
    def total_days(self):
        return self.rental.get_total_days()
    
    @property
    def total_amount(self):
        return self.quantity * self.daily_rate * self.total_days
    
    def __str__(self):
        return f"{self.tool.name} x {self.quantity}"
    
    class Meta:
        verbose_name = "Ijara mahsuloti"
        verbose_name_plural = "Ijara mahsulotlari"