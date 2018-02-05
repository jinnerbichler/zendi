from django.contrib import admin

from stellar.models import StellarAccount, StellarTransaction


class StellarAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'seed', 'address')


class StellarTransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'sender_address', 'receiver', 'receiver_address', 'amount')


admin.site.register(StellarAccount, StellarAccountAdmin)
admin.site.register(StellarTransaction, StellarTransactionAdmin)
