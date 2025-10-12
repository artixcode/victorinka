from django.shortcuts import render
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})

def home(request):
    return render(request, "core/home.html", {"title": "Quiz Platform"})
