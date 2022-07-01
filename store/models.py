from wsgiref.validate import validator
from django.db import models
from django.core.validators import MinValueValidator
from uuid import uuid4
from django.conf import settings

from store.validators import validate_file_size

# Create your models here.


class Category(models.Model):
    class Meta:
        ordering = ["title"]

    title = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.title


class Product(models.Model):
    class Meta:
        ordering = ["name"]

    name = models.CharField(max_length=255)
    description = models.TextField(null=True)
    available = models.BooleanField(default=False)
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    inventory = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self) -> str:
        return self.name

class ProductImages(models.Model):
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')
    
    image = models.ImageField(upload_to = 'store/images', validators=[validate_file_size])


class Customer(models.Model):
    BRONZE = "B"
    SILVER = "S"
    GOLD = "G"
    MEMBERSHIP_CHOICES = [(BRONZE, "Bronze"), (SILVER, "Silver"), (GOLD, "Gold")]
    phone = models.CharField(max_length=255)
    membership = models.CharField(
        max_length=1, choices=MEMBERSHIP_CHOICES, default=BRONZE
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        permissions = [("view_history", "Can view history")]

    def first_name(self):
        return self.user.first_name

    def last_name(self):
        return self.user.last_name

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"


class Order(models.Model):
    STATUS_PENDING = "P"
    STATUS_COMPLETE = "C"
    STATUS_FAILED = "F"
    PAYMENT_STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_COMPLETE, "Complete"),
        (STATUS_FAILED, "Failed"),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(
        max_length=1, choices=PAYMENT_STATUS_CHOICES, default=STATUS_PENDING
    )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    class Meta:
        unique_together = [["cart", "product"]]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
