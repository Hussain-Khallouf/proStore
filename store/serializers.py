from django.db import transaction
from rest_framework import serializers
from .models import (
    Cart,
    CartItem,
    Category,
    Customer,
    Order,
    OrderItem,
    ProductImages,
    Product,
    Review,
)

class ProductImagesServializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ['id','image']

    def create(self, validated_data):
        product_id = self.context["product_id"]
        return  ProductImages.objects.create(product_id=product_id, **validated_data)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "unit_price",'inventory', "category",'images']
        
    
    images = ProductImagesServializer(many=True,read_only=True)

    # price_with_tax = serializers.SerializerMethodField(method_name="calculate_tax")
    # category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    # category = serializers.HyperlinkedRelatedField(
    #     queryset=Category.objects.all(), view_name="category_details"
    # )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["title", "product_set"]

    product_set = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), many=True, required=False
    )

    # product_set = ProductSerializer(many=True)


class ReviewSerilaizer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["id", "name", "description", "date"]

    def create(self, validated_data):
        product_id = self.context["product_id"]
        return Review.objects.create(product_id=product_id, **validated_data)


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "unit_price"]


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "total_price"]

    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField(method_name="calcolate_total")

    def create(self, validated_data):
        cart_id = self.context["cart_id"]
        return CartItem.objects.create(cart_id=cart_id, **validated_data)

    def calcolate_total(self, cartitem):
        return cartitem.quantity * cartitem.product.unit_price


class CartSerilaizer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ["id", "created_at", "cartitem_set", "total"]

    id = serializers.UUIDField(read_only=True)
    cartitem_set = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField(method_name="calcolate_total")

    def create(self, validated_date):
        return Cart.objects.create(**validated_date)

    def calcolate_total(self, cart):
        return sum(
            [
                item.quantity * item.product.unit_price
                for item in cart.cartitem_set.all()
            ]
        )


class AddCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity"]

    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No product with geven ID")
        return value

    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        product_id = self.validated_data["product_id"]
        quantity = self.validated_data["quantity"]
        try:
            cartitem = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cartitem.quantity += quantity
            self.instance = cartitem
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data
            )
        return self.instance


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "user_id", "phone", "membership"]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price"]

    product = SimpleProductSerializer()


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "customer", "date", "payment_status", "orderitem_set"]

    orderitem_set = OrderItemSerializer(many=True, read_only=True)


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["payment_status"]


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(id=cart_id).exists():
            raise serializers.ValidationError("No cart with the given id")
        if CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError("The cart is empty")

        return cart_id

    def save(self, **kwargs):
        cart_id = self.validated_data["cart_id"]
        user_id = self.context["user_id"]
        with transaction.atomic():
            customer = Customer.objects.get(user_id=user_id)
            order = Order.objects.create(customer=customer)
            cart_items = CartItem.objects.select_related("product").filter(
                cart_id=cart_id
            )
            order_items = [
                OrderItem(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=item.product.unit_price,
                )
                for item in cart_items
            ]
            OrderItem.objects.bulk_create(order_items)
            Cart.objects.filter(id=cart_id).delete()
            return order
