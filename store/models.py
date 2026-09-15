from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('TEC', 'Tecnología'),
        ('ROPA', 'Vestuario'),
        ('HOG', 'Hogar & Deco'),
        ('ACC', 'Accesorios'),
    ]

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='TEC')
    stock = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.name} (${self.price})"

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"