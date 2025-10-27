from django.shortcuts import render
from .models import Person

def index(request):

    names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Heidi', 'Ivan', 'Judy', 'Karl', 'Liam']
    ages = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
    students = [{'name': name, 'age': age} for name, age in zip(names, ages)]
    

    return render(request, 'home/index.html', context={'students': students})
