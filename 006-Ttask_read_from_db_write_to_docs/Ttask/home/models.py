from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.age} years old)'
