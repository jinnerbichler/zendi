from django.contrib import admin

from web.models import UserFeedback


class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ('sender', 'email', 'message')


admin.site.register(UserFeedback, UserFeedbackAdmin)
