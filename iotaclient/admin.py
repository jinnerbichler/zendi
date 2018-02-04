from django.contrib import admin

from iotaclient.models import IotaSeed, IotaAddress, IotaTransaction, IotaBalance


class IotaSeedAdmin(admin.ModelAdmin):
    list_display = ('user', 'seed')


class IotaAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address')


class IotaBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')


class IotaTransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'bundle_hash', 'attachment_time', 'value', 'is_confirmed')


admin.site.register(IotaSeed, IotaSeedAdmin)
admin.site.register(IotaAddress, IotaAddressAdmin)
admin.site.register(IotaBalance, IotaBalanceAdmin)
admin.site.register(IotaTransaction, IotaTransactionAdmin)