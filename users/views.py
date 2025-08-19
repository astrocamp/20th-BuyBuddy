from django.shortcuts import render, get_object_or_404
from .models import User, UserAddress
from .forms import UserForm, UserAddressForm

def profiles(request, id):
    user = get_object_or_404(User, pk=id)
    user_address = get_object_or_404(UserAddress, user=user)
    user_form = UserForm(instance=user)
    user_address_form = UserAddressForm(instance=user_address)

    return render(request, "users/profiles.html", {"user_form":user_form, "user_address_form":user_address_form})
