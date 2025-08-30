from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Cart, CartItem

@receiver(user_logged_in)
def merge_carts(sender, user, request, **kwargs):
    # Get session-based cart (if any)
    session_key = request.session.session_key
    if not session_key:
        return  # No session cart to merge

    try:
        session_cart = Cart.objects.get(session_key=session_key)
    except Cart.DoesNotExist:
        return  # No session cart exists

    # Get or create user-based cart
    user_cart, created = Cart.objects.get_or_create(user=user)

    # Merge session cart items into user cart
    for session_item in session_cart.cartitem_set.select_related('product'):
        user_item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            product=session_item.product,
            defaults={'quantity': session_item.quantity}
        )
        if not created:
            # If item exists, add quantities
            user_item.quantity += session_item.quantity
            user_item.save()

    # Delete session cart after merging
    session_cart.delete()
    # Update session to point to user cart (optional, for consistency)
    request.session['cart_id'] = user_cart.id