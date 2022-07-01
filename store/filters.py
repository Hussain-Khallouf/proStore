from django_filters import FilterSet
from .models import Product


class ProductFilter(FilterSet):
    class Meta:
        model = Product
        fields = {
            "category_id": ["exact"],
            "unit_price": ["gt", "lt"],
            "available": ["exact"],
        }
