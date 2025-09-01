from django.db import models
from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, BaseUserManager
import uuid
from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
)


#Custom user manager here
#Manage customers, admins, and sellers with different permissions.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Please provide a valid email address.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        
        email = self.normalize_email(email)

        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_seller', False)

        #Validate the required flags
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self.create_user(email, password, **extra_fields)
    
    def create_seller(self, email, password=None, **extra_fields):
        
        email = self.normalize_email(email)

        extra_fields.setdefault('is_seller', True)

        #Validate the required flags
        if extra_fields.get('is_seller') is not True:
            raise ValueError('Seller must have is_seller=True.')

        return self.create_user(email, password, **extra_fields)
    
        

def get_profile_image_path(self, filename):
    return f'profile_images/{self.pk}/{"profile_image.png"}'



# Create your models here.
# Create customers, admins, and sellers with different permissions.
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(verbose_name="email", unique=True, blank=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_seller = models.BooleanField(default=False, null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True,null=True, blank=True)
    phone_number = models.CharField(validators=[phone_regex], max_length=15, blank=True)
    profile_image = models.ImageField(upload_to=get_profile_image_path, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    hide_email = models.BooleanField(default=True)
    

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
    
    def get_profile_image_filename(self):
        return str(self.profile_image)[str(self.profile_image).index(f'profile_image/{self.pk}/'):]
    



class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'Pending'
        PAID = 'Paid'
        SHIPPED = 'Shipped'
        DELIVERED = 'Delivered'
        CANCELLED = 'Cancelled'

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    @property
    def order_items(self):
        return self.orderitem_set.all()


    @property
    def total_price(self):
        return sum(item.item_subtotal for item in self.orderitem_set.all())


    def __str__(self):
        return f'Order {self.order_id} {self.status} made by {self.user.username} on {self.created_at}'
    


#Store multiple shipping/billing addresses per user
class Address(models.Model):
    class AddressType(models.TextChoices):
        BILLING = 'Billing'
        SHIPPING = 'Shipping'
        OTHER = 'Other'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)#Links to user model FK - One to many relation
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True)#Links to model model FK - One to One relation
    street_address = models.CharField(max_length=128)
    apartment_unit = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=50)
    country = models.CharField(max_length=100, default='Ghana')
    type = models.CharField(
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.BILLING
    )

    def __str__(self):
        return f'{self.street_address}, {self.city}, {self.region}'

#Manage Items Availabe for sale
class Product(models.Model):
    class Categories(models.TextChoices):
        ELECTRONICS = 'Electronics & Accessories'
        FASHION = 'Fashion & Apparel'
        HOME = 'Home & Living'
        BEAUTY = 'Beauty & Personal Care'
        SPORTS = 'Sports & Outdoors'
        BOOKS = 'Books & Stationery'
        TOYS = 'Toys & Baby Products'

    id =  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.CharField(max_length=40, choices=Categories.choices)

    @property
    def in_stock(self):
        return self.stock > 0
    
    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def get_total(self):
        return sum(item.subtotal for item in self.cartitem_set.all())

    def __str__(self):
        return f'Cart of {self.user.email}'

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.quantity * self.product.price
    
    def __str__(self):
        return f'{self.cart.user.email} added {self.quantity} x {self.product.name} to their cart'
    
    class Meta:
        unique_together = ('cart', 'product')
    


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='items')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    @property
    def item_subtotal(self):
        return self.quantity * self.price
    
    def __str__(self):
        return f'{self.quantity} x {self.product.name}'
    

class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = "Pending"
        COMPLETED = "Completed"
        FAILED = "Failed"
        REFUNDED = "Refunded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    transaction_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.transaction_id} total is {self.amount} for {self.user.username}'
    
    class Meta:
        ordering = ['-created_at']


class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} about {self.product.name}"