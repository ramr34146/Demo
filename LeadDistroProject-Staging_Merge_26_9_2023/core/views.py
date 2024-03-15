#django Imports 
from django.shortcuts import redirect, render
from django.views.generic import View


class HomeView(View):
    template_name = "core/home.html"

    def get(self, request, *args, **kwargs):
        return redirect('auth:home')
