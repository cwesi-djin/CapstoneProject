from django.urls import path
from .views import ProductListView,  ProductDetailView, CartView, CartUpdateView, CartRemoveView, CheckoutView, ProductListByCategoryView, CartAddView
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from . import views

urlpatterns = [
    path('', views.register, name='register'),
    path("home/", views.home, name="home"),
    path("login/", LoginView.as_view(template_name="api/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<str:category>/', ProductListByCategoryView.as_view(), name='product-list-by-category'),
    path('products/<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/<uuid:pk>/', CartAddView.as_view(), name='cart-add'),
    path('cart/update/<int:pk>/', CartUpdateView.as_view(), name='cart-update'),
    path('cart/remove/<int:pk>/', CartRemoveView.as_view(), name='cart-remove'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
]