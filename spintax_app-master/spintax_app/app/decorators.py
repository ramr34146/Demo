from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect


# def role_required(allowed_roles=[]):
#     def decorator(func):
#         def wrap(request, *args, **kwargs):
#             if False:
#                 return func(request, *args, **kwargs)
#             else:
#                 return HttpResponse('sdfr')
#
#         return wrap
#
#     return decorator


def role_required(inner_function):
    data = 'a'

    def wrapped_func(request, data, *args, **kwargs):
        if False:
            data = 'a'
            inner_function(request, data, *args, **kwargs)
            return True
        else:
            return PermissionDenied

    return wrapped_func


def check_user_login(func):
    def wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        else:
            return func(request, *args, **kwargs)

    return wrapped


def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        else:
            return view_func(request, *args, **kwargs)

    return wrapper


def context_change(view_func):
    def wrapper(*args, **kwargs):
        if False:
            return HttpResponse('abc')
        else:

            return view_func(*args, **kwargs)

    return wrapper


def context_custom(view_func):
    def wrapper(*args, **kwargs):
        result = ''
