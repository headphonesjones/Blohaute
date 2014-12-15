from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from changuito.forms import DeleteItemForm, UpdateQuantityForm


def shopping_cart(request):

    if request.method == "GET":
        return render(request, 'cart.html', {'cart': request.cart})


def remove_cart_item(request):
    if request.method == "POST":
        form = DeleteItemForm(request.POST)
        if form.is_valid():
            request.cart.remove_item(form.cleaned_data['pk'])
        return HttpResponseRedirect(reverse('cart'))


def update_quanity(request):
    if request.method == "POST":
        form = UpdateQuantityForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['quantity'] == 0:
                request.cart.remove_item(form.cleaned_data['pk'])
            else:
                request.cart.update_quantity(form.cleaned_data['pk'], form.cleaned_data['quantity'])
        else:
            print 'form invalid'
        return HttpResponseRedirect(reverse('cart'))


