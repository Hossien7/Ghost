from django.shortcuts import render

def login(request):
    return render(request, 'login_app/index.html', context={'name':'hello world!!!'})
