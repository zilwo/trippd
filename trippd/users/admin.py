from django.contrib import admin
from .models import Language, Notification, Profile, User

# Register your models here.


admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Language)
admin.site.register(Notification)
