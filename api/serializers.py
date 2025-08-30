from .models import Product, Order, OrderItem, CustomUser, CartItem, Cart, Payment, Review
from rest_framework import serializers

#User serializers
class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'


class PrivateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'is_seller']

#Product model serializer converts user instances to JSON
class ProductSerializer(serializers.ModelSerializer):
    seller = PublicUserSerializer(read_only=True)
    

    class Meta:
        model = Product
        fields = [
            'name',
            'price',
            'stock',
            'category',
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price cannot be zero or less input proper price.")
        return value
    
    def validate_stcok(self, value):
        if value <= 0:
            raise serializers.ValidationError("Stock cannot be zero or less input proper price.")
        return value

class OrderItemSerializers(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'product',
            'quantity',
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializers(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    user = PublicUserSerializer(read_only=True)

    def get_total_price(self, obj):
        order_items = obj.items.all()
        return sum(order_item.subtotal for order_item in order_items)

    class Meta:
        model = Order
        fields = [
            'order_id',
            'user',
            'created_at',
            'updated_at',
            'status',
            'items',
            'total_price',
        ]

class CartItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        field = ['product','quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.quantity * obj.product.price
    

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        field = ['id', 'user', 'items', 'total_price']

    def get_total_price(self, obj):
        return sum([item.quantity * item.product.price for item in obj.items.all()])
    
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        field = ['id', 'order', 'amount', 'status', 'transaction_id', 'payment_method', 'created_at']




class ReviewSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = Review
        field = ['product', 'user', 'comment', 'created']