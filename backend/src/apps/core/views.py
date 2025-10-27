from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache

index = never_cache(TemplateView.as_view(template_name='index.html'))

def health(request):
    return JsonResponse({"status": "ok"})

def home(request):
    return render(request, "core/home.html", {"title": "Quiz Platform"})

