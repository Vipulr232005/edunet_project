from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from .models import DailyLog, DietDayLog, NotificationPreference, ReminderLog


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'cycle_day', 'steps', 'wellness_score', 'mood', 'weight_kg')
    list_filter = ('date',)
    search_fields = ('user__username',)
    date_hierarchy = 'date'
    ordering = ('-date',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs


@admin.register(DietDayLog)
class DietDayLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'early_morning', 'breakfast', 'mid_morning', 'lunch', 'evening_snack', 'dinner', 'bedtime')
    list_filter = ('date',)
    search_fields = ('user__username',)
    date_hierarchy = 'date'
    ordering = ('-date',)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'events_workshops', 'health_tips', 'app_updates',
        'breakfast_reminder', 'water_reminder', 'stretch_reminder', 'daily_log_reminder',
    )
    search_fields = ('user__username', 'user__email')


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'reminder_type')
    list_filter = ('reminder_type', 'date')
    search_fields = ('user__username',)
    date_hierarchy = 'date'
    ordering = ('-date',)


# Unregister default User admin so we can add "new users today" tracking
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """User admin with tracking for new users (filter by date joined, e.g. Today)."""
    list_display = (*BaseUserAdmin.list_display, 'date_joined')
    list_filter = (*BaseUserAdmin.list_filter, 'date_joined')
    ordering = ('-date_joined',)
    change_list_template = 'admin/auth/user/change_list_with_new_users.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        today = timezone.localdate()
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        new_users_today = UserModel.objects.filter(
            date_joined__date=today
        ).count()
        extra_context['new_users_today'] = new_users_today
        extra_context['new_users_today_label'] = 'New users today'
        return super().changelist_view(request, extra_context=extra_context)
