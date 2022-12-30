from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username', 'email']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','title']

class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)
    category = CategorySerializer(read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id','title','price','featured','category','category_id']

class MenuItemSimpleSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    class Meta:
        model = MenuItem
        fields = ['id','title','price','category']

class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    menuitem = MenuItemSimpleSerializer(read_only=True)
    user_id = serializers.IntegerField()
    menuitem_id = serializers.IntegerField()

    class Meta:
        model = Cart
        fields = ['user','menuitem','quantity','unit_price','price','user_id','menuitem_id']
        
class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    delivery_crew = UserSerializer(read_only=True)
    user_id = serializers.IntegerField()
    delivery_crew_id = serializers.IntegerField(default=None)
    
    class Meta:
        model = Order
        fields = ['id','user','user_id','delivery_crew','delivery_crew_id','status','total','date']

class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    menuitem = MenuItemSimpleSerializer(read_only=True)
    order_id = serializers.IntegerField()
    menuitem_id = serializers.IntegerField()
    class Meta:
        model = OrderItem
        fields = ['id','order','menuitem','quantity','unit_price','price','menuitem_id','order_id']

