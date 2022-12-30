from django.urls import path
from . import views

urlpatterns = [
    path('users', views.CustomerView.as_view()),
    path('groups/manager/users', views.ManagerManagementView.as_view({'get':'list','post':'create'})),
    path('groups/manager/users/<int:pk>', views.ManagerManagementView.as_view({'get':'retrieve','delete':'destroy'})),
    path('groups/delivery-crew/users', views.DeliveryCrewManagement.as_view({'get':'list','post':'create'})),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryCrewManagement.as_view({'get':'retrieve','delete':'destroy'})),
    path('categories',views.CategoriesView.as_view()),
    path('menu-items', views.MenuItemView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('cart/menu-items', views.CartView.as_view()),
    path('orders', views.OrderView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
]
