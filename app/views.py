from django.contrib import auth
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from app.models import AppUser, StaticVendor, AmbulantVendor, Product, Vendor, Buyer

from app.Forms import LoginForm, EditVendorForm, EditProductForm


def index(req):
    return render(req, 'app/index.html', {})


def login(request):
    form = LoginForm(request.POST)
    if form.is_valid() and request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        # app_user = AppUser.objects.filter(user=user)
        # print username, password, user
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect('home.html')
            else:
                return render(request, 'app/login.html', {
                    'login_message': 'The user has been removed', 'form': form, })
        else:
            return render(request, 'app/login.html', {
                'login_message': 'Enter the username and password correctly', 'form': form, })
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {
        'form': form,
    })


def signup(req):
    return render(req, 'app/signup.html', {})


def products_administration(request):
    if request.user.is_authenticated():
        user = User.objects.get(username=request.user.username)
        app_user = AppUser.objects.get(user=user)
        if app_user.user_type != 'C':
            return render(request, 'app/gestion-productos.html',
                          {'image': app_user.photo, 'user': user.username,
                           'is_static': True if app_user.user_type == 'VF' else False})
        else:
            return HttpResponseRedirect(reverse('home'))
    else:
        return HttpResponseRedirect(reverse('index'))


def home(request):
    if request.user.is_authenticated():
        username = request.user.username
        app_user = AppUser.objects.get(user=request.user)
        # print app_user[0].user_type, type(app_user[0].user_type)
        if app_user.user_type == u'C':
            return render(request, 'app/home.html', {'user': username})
        else:
            vendor = Vendor.objects.get(user=app_user)
            update(vendor)
            products = []
            raw_products = Product.objects.filter(vendor=vendor)
            for i, p in enumerate(raw_products):
                tmp = {
                    'icon': p.icon,
                    'name': p.name,
                    'id': 'modal' + str(i),
                    'image': p.photo,
                    'category': p.category_str(),
                    'stock': p.stock,
                    'desc': p.description,
                    'price': p.price,
                    'pid': p.id
                }
                products.append(tmp)

            data = {
                'user': username,
                'image': app_user.photo,
                'name': app_user.user.first_name,
                'is_static': True if vendor.user.user_type == 'VF' else False,
                'last_name': app_user.user.last_name,
                'state': 'Activo' if vendor.state == 'A' else 'Inactivo',
                'payment': vendor.payment_str(),
                'fav': vendor.times_favorited,
                'schedule': StaticVendor.objects.get(
                    user=vendor.user).schedule() if vendor.user.user_type == 'VF' else "",
                'type': 'Vendedor Fijo' if vendor.user.user_type == 'VF' else 'Vendedor Ambulante',
                'products': products
            }
            return render(request, 'app/vendedor-profile-page.html', data)
    else:
        return HttpResponseRedirect('login.html')


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('index'))


def edit_account(request):
    if request.user.is_authenticated():
        form = EditVendorForm(request.POST, request.FILES)
        user = User.objects.get(username=request.user.username)
        app_user = AppUser.objects.get(user=user)

        if app_user.user_type == u'C':
            return HttpResponseRedirect(reverse('home'))
        if form.is_valid() and request.method == 'POST':
            user.first_name = request.POST['name']
            user.last_name = request.POST['last_name']
            if form.cleaned_data['photo'] is not None:
                app_user.photo = form.cleaned_data['photo']
                app_user.save()
            user.save()
            return HttpResponseRedirect('home')
        else:
            form = EditVendorForm(initial={'name': request.user.first_name, 'last_name': request.user.last_name})
        data = {'form': form, 'image': app_user.photo, 'is_static': True if app_user.user_type == 'VF' else False}
        return render(request, 'app/edit_account.html', data)
    else:
        return HttpResponseRedirect(reverse('index'))


def stock(request):
    if request.user.is_authenticated():
        username = request.user.username
        app_user = AppUser.objects.get(user=request.user)
        # print app_user[0].user_type, type(app_user[0].user_type)
        if app_user.user_type == u'C':
            return render(request, 'app/home.html', {'user': username})
        else:
            vendor = Vendor.objects.get(user=app_user)
            products = []
            raw_products = Product.objects.filter(vendor=vendor)
            for i, p in enumerate(raw_products):
                tmp = {
                    'icon': p.icon,
                    'name': p.name,
                    'id': 'modal' + str(i),
                    'image': p.photo,
                    'category': p.category_str(),
                    'stock': p.stock,
                    'desc': p.description,
                    'price': p.price,
                    'pid': p.id
                }
                products.append(tmp)

            data = {
                'user': username,
                'image': app_user.photo,
                'is_static': True if app_user.user_type == 'VF' else False,
                'products': products
            }
            return render(request, 'app/stock.html', data)
    else:
        return HttpResponseRedirect('login.html')


def edit_products(request, pid):
    if request.user.is_authenticated():
        user = User.objects.get(username=request.user.username)
        app_user = AppUser.objects.get(user=user)

        if app_user.user_type != 'C':
            vendor = Vendor.objects.get(user=app_user)
            products = Product.objects.filter(vendor=vendor)
            try:
                product = products.get(id=pid)
                form = EditProductForm(request.POST, request.FILES)
                if request.method == 'POST' and form.is_valid():
                    product.name = form.cleaned_data['name']
                    product.price = form.cleaned_data['price']
                    product.stock = form.cleaned_data['stock']
                    product.description = form.cleaned_data['des']
                    if form.cleaned_data['photo'] is not None:
                        product.photo = form.cleaned_data['photo']
                    product.save()
                    return HttpResponseRedirect(reverse('home'))
                else:
                    form = EditProductForm(initial={'name': product.name, 'price': product.price,
                                                    'stock': product.stock, 'des': product.description})
                    data = {'form': form, 'photo': product.photo, 'image': app_user.photo}
                    return render(request, 'app/edit_product.html', data)
            except:
                return HttpResponseRedirect(reverse('home'))

    else:
        return HttpResponseRedirect(reverse('index'))


def vendor_c(request, pid):
    data = {'is_fav': False}
    try:
        vendor = Vendor.objects.get(id=pid)
        update(vendor)
        if request.user.is_authenticated():
            user = AppUser.objects.get(user=request.user)
            data['auth'] = True
            data['user'] = request.user.username
            data['u_image'] = user.photo
            if user.user_type == 'C':
                buyer = Buyer.objects.get(user=user)
                for i in buyer.favorites.values():
                    if i == vendor:
                        data['is_fav'] = True
        else:
            data['auth'] = False

        products = []
        raw_products = Product.objects.filter(vendor=vendor)
        for i, p in enumerate(raw_products):
            tmp = {
                'icon': p.icon,
                'name': p.name,
                'id': 'modal' + str(i),
                'image': p.photo,
                'category': p.category_str(),
                'stock': p.stock,
                'desc': p.description,
                'price': p.price,
            }
            products.append(tmp)
        data['image'] = vendor.user.photo
        data['name'] = vendor.user.user.first_name
        data['last_name'] = vendor.user.user.last_name
        data['state'] = 'Activo' if vendor.state == 'A' else 'Inactivo'
        data['payment'] = vendor.payment
        data['fav'] = vendor.times_favorited
        data['schedule'] = StaticVendor.objects.get(user=vendor.user).schedule if vendor.user.user_type == 'VF' else ""
        data['type'] = 'Vendedor Fijo' if vendor.user.user_type == 'VF' else 'Vendedor Ambulante'
        data['products'] = products

        return render(request, 'app/vendor_info.html', data)
    except:
        return HttpResponseRedirect(404)


"""
TODO: hacer el update
"""


def update():
    pass
