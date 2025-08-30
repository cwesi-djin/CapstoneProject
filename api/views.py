from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from .models import Product, Cart, CartItem, Order, OrderItem
from django.views.generic import View
from django.contrib import messages
from django.http import Http404



User = get_user_model()

def home(request):
    return render(request, "api/home.html")

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "api/register.html", {"form": form})

def login_view(request):
    return render(request, 'api/login.html')

def logout(request):
    return render(request, 'api/login.html')

class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'
    ordering = ['category', 'price']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Product.Categories.choices
        return context
    
    def get_queryset(self):
        return Product.objects.filter(stock__gt=0).select_related('seller')
    
class ProductDetailView(DetailView):
    model = Product
    template_name = 'product/product_detail.html'
    context_object_name = 'product'
    pk_url_kwarg = 'pk'


class ProductListByCategoryView(ListView):
    model = Product
    template_name = 'api/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        category = self.kwargs['category']
        if category not in dict(Product.Categories.choices):
            raise Http404("Invalid category")
        return Product.objects.filter(category=category, stock__gt=0).select_related('seller')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Product.Categories.choices
        context['current_category'] = self.kwargs['category']
        return context

class CartAddView(View):
    def post(self, request, pk):
        product = get_object_or_404(Product, id=pk)
        if not product.in_stock:
            messages.error(request, f"{product.name} is out of stock")
            return redirect('product-list')
        cart = self.get_cart()
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            if cart_item.quantity + 1 > product.stock:
                messages.error(request, f"Cannot add more {product.name}. Only {product.stock} left in stock")
                return redirect('product-list')
            cart_item.quantity += 1
            cart_item.save()
        messages.success(request, f"{product.name} was added successfully")
        return redirect('cart')
    def get_cart(self):
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user= self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session = self.request.session.session_key
            cart, created =  Cart.objects.get_or_create(session_key=session_key)
        return cart
        

class CartView(ListView):
    template_name = 'cart.html'
    context_object_name = 'cart_items'

    def get_queryset(self):
        cart = self.get_cart()
        return cart.cart_item.set.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.cart()
        context['total'] = cart.get_total()
        return context
    
    def get_cart(self):
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart
    

class CartUpdateView(View):
    def post(self, request, pk):
        cart = self.get_cart()
        cart_item = get_object_or_404(CartItem, pk=pk, cart=cart)
        quantity = request.POST.get('quantity', 1)
        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError("Quantity must be at least 1")
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f"Updated {cart_item.product.name} quantity to {quantity}.")
        except ValueError as e:
            messages.error(request, f"Invalid quantity: {e}")
        return redirect('cart')
    
    def get_cart(self):
        # Same as in CartView
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart
    


class CartRemoveView(View):
    def post(self, request, pk):
        cart = self.get_cart()
        cart_item = get_object_or_404(CartItem, pk=pk, cart=cart)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f"Removed {product_name} from cart.")
        return redirect('cart')

    def get_cart(self):
        # Same as in CartView
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key)
        return cart
    

class CheckoutView(TemplateView):
    template_name = 'api/checkout.html'

    def get_cart(self):
        if self.request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=self.request.user)
        else:
            if not self.request.session.session_key:
                self.request.session.create()
            session_key = self.request.session.session_key
            cart, _ = Cart.objects.get_or_create(session_key=session_key)
        return cart

    def get(self, request, *args, **kwargs):
        cart = self.get_cart()
        if not cart.cartitem_set.exists():
            return redirect("cart")  # safe redirect here

        context = self.get_context_data(cart=cart)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = kwargs.get("cart") or self.get_cart()
        context['cart_items'] = cart.cartitem_set.all()
        context['total'] = cart.get_total()
        return context

    def post(self, request, *args, **kwargs):
        cart = self.get_cart()
        if not cart.cartitem_set.exists():
            return redirect("cart")

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            total=cart.get_total()
        )

        for item in cart.cartitem_set.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        cart.cartitem_set.all().delete()  # clear cart
        return redirect("order-success", pk=order.pk)


class OrderSuccessView(DetailView):
    model = Order
    template_name = "shop/order_success.html"



def product_list(request, category_slug=None):
    categories = Product.Categories.objects.all()
    products = Product.objects.all()

    if category_slug:  # only filter if user clicked a category link
        category = get_object_or_404(Product.Categories, slug=category_slug)
        products = products.filter(category=category)
    else:
        category = None

    return render(request, "product_list.html", {
        "categories": categories,
        "products": products,
        "current_category": category,
    })