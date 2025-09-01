from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from .views import (
    register,
    home,
    create_product,
    ProductListView,
    ProductDetailView,
    ProductListByCategoryView,
    CartView,
    CartAddView,
    CartUpdateView,
    CartRemoveView,
    CheckoutView,
)

urlpatterns = [
    path('', register, name='register'),
    path("home/", home, name="home"),
    path("login/", LoginView.as_view(template_name="api/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Product URLs
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/category/<str:category>/', ProductListByCategoryView.as_view(), name='product-list-by-category'),
    path('products/<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/create/', create_product, name='product-create'),
    # Cart URLs
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/<uuid:pk>/', CartAddView.as_view(), name='cart-add'),
    path('cart/update/<uuid:pk>/', CartUpdateView.as_view(), name='cart-update'),
    path('cart/remove/<uuid:pk>/', CartRemoveView.as_view(), name='cart-remove'),

    # Checkout
    path('checkout/', CheckoutView.as_view(), name='checkout'),
]