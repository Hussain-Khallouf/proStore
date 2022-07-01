from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.mixins import (
    CreateModelMixin,
    UpdateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
)
from rest_framework.permissions import (
    IsAdminUser,
    DjangoModelPermissions,
    IsAuthenticated,
)
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.decorators import action

from store.filters import ProductFilter
from store.pagination import StanderedPagenation
from store.permisions import IsAdminOrReadOnly, ViewHistoryPermission
from store.serializers import CustomerSerializer
from .models import (
    Cart,
    CartItem,
    Category,
    Customer,
    Order,
    Product,
    ProductImages,
    OrderItem,
    Review,
)
from .serializers import (
    AddCartItemSerializer,
    CartItemSerializer,
    CartSerilaizer,
    CategorySerializer,
    CreateOrderSerializer,
    OrderSerializer,
    ProductImagesServializer,
    ProductSerializer,
    ReviewSerilaizer,
    UpdateCartItemSerializer,
    UpdateOrderSerializer,
)


@api_view()
def index(request):
    queruset = Cart.objects.all()
    return Response(queruset[0])


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.prefetch_related('images').all()
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    pagination_class = StanderedPagenation
    permission_classes = [DjangoModelPermissions]
    search_fields = ["name"]
    ordering_fields = ["unit_price"]

    def get_serializer_context(self):
        return {"request": self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs["pk"]).count() > 0:
            return Response({"error": "You cannot delete object with related objets"})

        return super().destroy(request, *args, **kwargs)


class ProductImagesViewSet(ModelViewSet):
    serializer_class = ProductImagesServializer

    def get_queryset(self):
        return ProductImages.objects.filter(product_id = self.kwargs['product_pk'])

    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.prefetch_related("product_set").all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_context(self):
        return {"request": self.request}

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(category_id=kwargs["pk"]).count() > 0:
            return Response({"error": "You cannot delete object with related objets"})
        return super().destroy(request, *args, **kwargs)


class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerilaizer

    def get_queryset(self):
        return Review.objects.all().filter(product_id=self.kwargs["product_pk"])

    def get_serializer_context(self):
        return {"product_id": self.kwargs["product_pk"]}


class CartViewSet(
    GenericViewSet,
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    RetrieveModelMixin,
):
    queryset = Cart.objects.prefetch_related("cartitem_set").all()
    serializer_class = CartSerilaizer


class CartItemViewSet(ModelViewSet):
    http_method_names = ["get", "post", "put", "delete"]
    serializer_class = CartItemSerializer

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PUT":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_queryset(self):
        cart_id = self.kwargs["cart_pk"]
        return CartItem.objects.select_related("product").filter(cart_id=cart_id)

    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"]}

class CustomerViewSet(
    CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet
):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    @action(detail=True, permission_classes=[ViewHistoryPermission])
    def history(self, request, pk):
        return Response("ok")

    @action(detail=False, methods=["GET", "PUT"], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer = Customer.objects.get(user_id=request.user.id)
        if request.method == "GET":
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class OrderViewSet(ModelViewSet):
    def get_permissions(self):
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        elif self.request.method == "PUT":
            return UpdateOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data, context={"user_id": self.request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        else:
            customer_id = Customer.objects.only("id").get(user_id=user.id)
            return Order.objects.filter(customer_id=customer_id)
