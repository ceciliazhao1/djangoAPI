from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth.models import User, Group
from .permissions import IsManagerUser, IsDeliveryCrewUser, IsCustomerUser
from rest_framework import status
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer
from datetime import date


# Create your views here.
        
class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes =[authentication.TokenAuthentication]
    ordering_fields = ["order_id"]
    search_fields = ["order__status"]
    

    def get_queryset(self):
        if self.request.user.groups.filter(name='Customer').exists():
            return OrderItem.objects.select_related("order", "menuitem").all()
        else:
            return Order.objects.select_related("user", "delivery_crew").all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderItemSerializer
        else:
            return OrderSerializer

    def get_permissions(self):
        self.permission_classes = [permissions.IsAdminUser]
        if self.request.method == 'GET':
            self.permission_classes = [permissions.IsAdminUser|IsCustomerUser]
        elif self.request.method in ['PUT','DELETE']:
            self.permission_classes= [permissions.IsAdminUser|IsManagerUser]
        elif self.request.method == 'PATCH':
            self.permission_classes= [permissions.IsAdminUser|IsManagerUser|IsDeliveryCrewUser]
        return super().get_permissions()

    def retrieve(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        if order.user != request.user:
            return Response({"message": "Not allowed to view this order"}, status.HTTP_403_FORBIDDEN)

        order_items = self.get_queryset().filter(order_id=pk)
        response_order_items = OrderItemSerializer(order_items, many=True)
        return Response(response_order_items.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        if request.user.groups.filter(name='Manager').exists():
            return super().partial_update(request, pk)
        else:
            if not "status" in request.data:
                return Response({"message":"No status provided"}, status.HTTP_400_BAD_REQUEST)
            status_field = request.data['status']
            updated_order = OrderSerializer(order, data={"status": status_field}, partial=True)
            updated_order.is_valid()
            updated_order.save()
            return Response(updated_order.data, status.HTTP_200_OK)

class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    authentication_classes = [authentication.TokenAuthentication]
    ordering_fields = ["status", "total"]
    search_fields = ["user__username", "delivery_crew__username"]
    filterset_fields = ['status']

    def get_queryset(self):
    
        if self.request.user.groups.filter(name='Manager').exists():
            return Order.objects.select_related("user", "delivery_crew").all()
        elif self.request.user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.select_related("user", "delivery_crew").filter(delivery_crew=self.request.user)
        elif self.request.user.groups.filter(name='Customer').exists():
            return Order.objects.select_related("user", "delivery_crew").filter(user=self.request.user)

        return super().get_queryset()


    def get_permissions(self):
        self.permission_classes = [permissions.IsAdminUser|IsManagerUser|IsDeliveryCrewUser|IsCustomerUser]
        if self.request.method == 'POST':
            self.permission_classes = [permissions.IsAdminUser|IsCustomerUser]

        return super().get_permissions()

    def post(self, request):
        cart = Cart.objects.select_related("user", "menuitem").filter(user=request.user)
        if not cart.exists():
            return Response({"message": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        total = 0
        order = OrderSerializer(data={"user_id": request.user.id, "total": total, "date": date.today()})
        order.is_valid()
        order.save()
        order_id = Order.objects.all().order_by("-id").first().id

        for cart_item in cart:
            total += float(cart_item.price)
            orderitem = OrderItemSerializer(data={"order_id":order_id, "menuitem_id":cart_item.menuitem_id, "quantity":cart_item.quantity, "unit_price":cart_item.unit_price, "price":cart_item.price})
            orderitem.is_valid(raise_exception=True)
            orderitem.save()
            cart_item.delete()

        order = OrderSerializer(Order.objects.get(id=order_id), data={"total": total}, partial=True)
        order.is_valid()
        order.save()
        return Response(order.data, status=status.HTTP_200_OK)        

class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    serializer_class = CartSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser|IsCustomerUser]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def post(self, request):
        
        if not "menuitem_id" in request.POST:
             return Response({"message": "Not menu item ID provided"}, status=status.HTTP_400_BAD_REQUEST)

        if not "quantity" in request.POST:
            return Response({"message": "Not quantity provided"}, status=status.HTTP_400_BAD_REQUEST)

        menuitem = get_object_or_404(MenuItem, id=request.POST["menuitem_id"])        
        quantity = request.POST["quantity"]
       
        cart = CartSerializer(data={"user_id":request.user.id, "menuitem_id":menuitem.id, "quantity":quantity, "unit_price":menuitem.price, "price":int(quantity)*menuitem.price})
        cart.is_valid(raise_exception=True)
        cart.save()
        return Response(cart.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response({"message": "Cart Deleted"}, status=status.HTTP_200_OK)
      
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    authentication_classes = [authentication.TokenAuthentication]

    def get_permissions(self):
        self.permission_classes = [permissions.IsAdminUser|IsManagerUser|IsCustomerUser|IsDeliveryCrewUser]
        if self.request.method != 'GET':
            self.permission_classes = [permissions.IsAdminUser|IsManagerUser]
        return super().get_permissions()

class MenuItemView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    ordering_fields=['price','title']
    search_fields=['title', 'category__title']
    filterset_fields = ['category']
    authentication_classes = [authentication.TokenAuthentication]
    
        
    def get_permissions(self):
        self.permission_classes = [permissions.IsAdminUser|IsManagerUser|IsCustomerUser|IsDeliveryCrewUser]
        if self.request.method != 'GET':
            self.permission_classes = [permissions.IsAdminUser|IsManagerUser]
        return super().get_permissions()

class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    authentication_classes = [authentication.TokenAuthentication]

    def get_permissions(self):
        self.permission_classes = [permissions.IsAdminUser|IsManagerUser|IsCustomerUser|IsDeliveryCrewUser]
        if self.request.method != 'GET':
            self.permission_classes = [permissions.IsAdminUser|IsManagerUser]
        return super().get_permissions()
    
class ManagerManagementView(ViewSet):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser|IsManagerUser]

    def list(self, request):
        users = [{'email':user.email,'id':user.id,'username':user.username} for user in User.objects.filter(groups__name="Manager")]
        return Response(users)

    def create(self, request):
        username = request.data['username']
    
        if not username:
            return Response('Not username provided', status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, username=username)
        if user.groups.filter(name='Customer').exists():
            customers = Group.objects.get(name="Customer")
            customers.user_set.remove(user)

        managers = Group.objects.get(name="Manager")
        managers.user_set.add(user)
        
        return Response(f'User {username} added to Managers', status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        if not pk:
            return Response('Not id provided', status.HTTP_400_BAD_REQUEST)
    
        user = get_object_or_404(User, id=pk)

        return Response({'email':user.email,'id':user.id,'username':user.username}, status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        if not pk:
            return Response('Not id provided', status.HTTP_400_BAD_REQUEST)
    
        user = get_object_or_404(User, id=pk)
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)        
        
        return Response(f'User {user.username} removed from Manager group', status.HTTP_200_OK)

class DeliveryCrewManagement(ViewSet):

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser|IsManagerUser]

    def list(self, request):
        users = [{'email':user.email,'id':user.id,'username':user.username} for user in User.objects.filter(groups__name="Delivery Crew")]
        return Response(users, status.HTTP_200_OK)

    def create(self, request):
        username = request.data['username']
    
        if not username:
            return Response('Not username provided', status.HTTP_400_BAD_REQUEST)
        
        user = get_object_or_404(User, username=username)

        if user.groups.filter(name='Customer').exists():
            customers = Group.objects.get(name="Customer")
            customers.user_set.remove(user)

        managers = Group.objects.get(name="Delivery Crew")
        managers.user_set.add(user)
        
        return Response(f'User {username} added to Delivery Crew', status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        if not pk:
            return Response('Not id provided', status.HTTP_400_BAD_REQUEST)
    
        user = get_object_or_404(User, id=pk)

        return Response({'email':user.email,'id':user.id,'username':user.username}, status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        if not pk:
            return Response('Not id provided', status.HTTP_400_BAD_REQUEST)
    
        user = get_object_or_404(User, id=pk)

        managers = Group.objects.get(name="Delivery Crew")
        managers.user_set.remove(user)        
        
        return Response(f'User {user.username} removed from Delivery Crew group', status.HTTP_200_OK)

class CustomerView(generics.CreateAPIView):
    def post(self, request):
        if not "username" in request.data:
            return Response({'message':'Not username provided'}, status.HTTP_400_BAD_REQUEST)
        if not "password" in request.data:
            return Response({'message':'Not password provided'}, status.HTTP_400_BAD_REQUEST)
        if not "email" in request.data:
            email = ""
        else:
            email = request.data['email']

        if  User.objects.filter(username='foo').exists():
            return Response({'message':'User already exists'}, status.HTTP_400_BAD_REQUEST)

        user=User.objects.create_user(username=request.data['username'], email=email, password=request.data['password']) 
        user.save()

        customers = Group.objects.get(name="Customer")
        customers.user_set.add(user)

        return Response({'message':'user created'}, status.HTTP_201_CREATED)
        

