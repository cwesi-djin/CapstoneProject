from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import login
from .models import Product, Cart, CartItem, Order
from .forms import ProductForm, CustomUserCreationForm
from django.contrib import messages


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # automatically log's the user in after registration
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "api/register.html", {"form": form})


def home(request):
    return render(request, "api/home.html")

def is_seller(user):
    return user.role == "seller" or user.is_superuser

@user_passes_test(is_seller)
def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user  # Set the seller to the current user
            product.save()
            messages.success(request, f"Product '{product.name}' created successfully.")
            return redirect('product-list')
        else:
            messages.error(request, "Error creating product. Please check the form.")
    else:
        form = ProductForm()
    
    return render(request, 'api/product_create.html', {'form': form})


class ProductListView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, "api/product_list.html", {"products": products})

class ProductDetailView(View):
    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        return render(request, "api/product_detail.html", {"product": product})

class ProductListByCategoryView(View):
    def get(self, request, category):
        products = Product.objects.filter(category__iexact=category)
        return render(request, "api/product_list.html", {"products": products, "category": category})
    


@method_decorator(login_required, name="dispatch")
class CartView(View):
    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        return render(request, "api/cart.html", {"cart": cart})

@method_decorator(login_required, name="dispatch")
class CartAddView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity += 1
        cart_item.save()
        return redirect("cart")

@method_decorator(login_required, name="dispatch")
class CartUpdateView(View):
    def post(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        quantity = int(request.POST.get("quantity", 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        return redirect("cart")

@method_decorator(login_required, name="dispatch")
class CartRemoveView(View):
    def post(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        cart_item.delete()
        return redirect("cart")
    
@method_decorator(login_required, name="dispatch")
class CheckoutView(View):
    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        if cart.items.exists():
            order = Order.objects.create(user=request.user)
            for item in cart.items.all():
                order.items.create(product=item.product, quantity=item.quantity)
            cart.items.all().delete()  # clear cart after checkout
            return render(request, "api/checkout_success.html", {"order": order})
        return redirect("cart")