from django.contrib import admin
from .models import Language, Notification, Profile, SavedPlace, User, Rating

# Register your models here.


admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Language)
admin.site.register(Notification)
admin.site.register(Rating)
admin.site.register(SavedPlace)
