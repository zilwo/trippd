from django.contrib import admin
from .models import Trip, TripMembership, TripGroup, TripGroupMessage

# Register your models here.
admin.site.register(Trip)
admin.site.register(TripMembership)
admin.site.register(TripGroup)
admin.site.register(TripGroupMessage)
