from django.db.models import Count
from django.contrib import admin
from django.http import HttpRequest
from .models import Category, Customer, Order, OrderItem, Product
from django.utils.html import format_html, urlencode
from django.urls import reverse

# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # fields = ['name']
    autocomplete_fields = ["category"]
    list_display = ["name", "unit_price", "inventory_status", "category_title"]
    list_editable = ["unit_price"]
    list_select_related = ["category"]
    list_per_page = 10
    list_filter = ["unit_price"]
    search_fields = ["name"]

    @admin.display(ordering="inventory")
    def inventory_status(self, product):
        if product.inventory < 10:
            return "Low"
        return "OK"

    def category_title(self, product):
        return product.category.title


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "membership", "orders_count"]
    ordering = []
    list_select_related = ["user"]
    list_editable = ["membership"]
    list_per_page = 10
    search_fields = ["first_name__istartswith", "last_name__istartswith"]

    @admin.display(ordering="orders_count")
    def orders_count(self, customer):
        url = (
            reverse("admin:store_order_changelist")
            + "?"
            + urlencode({"customer__id": str(customer.id)})
        )
        return format_html('<a href="{}">{}</a>', url, customer.orders_count)

    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).annotate(orders_count=Count("order"))


class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ["product"]
    model = OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["customer", "date", "payment_status"]
    autocomplete_fields = ["customer"]
    inlines = [OrderItemInline]
    ordering = ["date"]
    list_per_page = 100


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["title", "products_count"]
    search_fields = ["title"]

    @admin.display(ordering="products_count")
    def products_count(self, category):
        return category.products_count

    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).annotate(products_count=Count("product"))
