from django.contrib import admin

from wallet.models import IotaSeed, IotaAddress, IotaExecutedTransaction


class IotaSeedAdmin(admin.ModelAdmin):
    list_display = ('user', 'seed')


class IotaAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'attached')


class IotaExecutedTransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'execution_time', 'transaction_hash', 'value', 'message')


admin.site.register(IotaSeed, IotaSeedAdmin)
admin.site.register(IotaAddress, IotaAddressAdmin)
admin.site.register(IotaExecutedTransaction, IotaExecutedTransactionAdmin)
