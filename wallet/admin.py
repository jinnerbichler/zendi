from django.contrib import admin

from wallet.models import IotaSeed


class IotaSeedAdmin(admin.ModelAdmin):
    list_display = ('user', 'seed')


admin.site.register(IotaSeed, IotaSeedAdmin)
