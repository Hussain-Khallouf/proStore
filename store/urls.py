from django.urls import path, include
from . import views
from rest_framework_nested import routers


router = routers.DefaultRouter()
router.register("products", views.ProductViewSet, basename="products")
router.register("categories", views.CategoryViewSet, basename="categories")
router.register("carts", views.CartViewSet, basename="carts")
router.register("customers", views.CustomerViewSet, basename="customers")
router.register("orders", views.OrderViewSet, basename="orders")

products_router = routers.NestedDefaultRouter(router, "products", lookup="product")
products_router.register("reviews", views.ReviewViewSet, basename="product-reviews")
products_router.register("images", views.ProductImagesViewSet, basename="product-images")


carts_router = routers.NestedDefaultRouter(router, "carts", lookup="cart")
carts_router.register("cartitems", views.CartItemViewSet, basename="cartitems")



urlpatterns = router.urls + products_router.urls + carts_router.urls

# urlpatterns = [
#     # path("", views.index),
#    path('',include(router.urls))
# ]
