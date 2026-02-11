from django.db import models
from django.conf import settings


class DailyLog(models.Model):
    """One log per user per day – all metrics and graph data."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_logs',
    )
    date = models.DateField(db_index=True)
    # Metrics
    cycle_day = models.PositiveSmallIntegerField(null=True, blank=True)
    steps = models.PositiveIntegerField(null=True, blank=True, default=0)
    water_glasses = models.PositiveSmallIntegerField(null=True, blank=True, default=0)
    wellness_score = models.PositiveSmallIntegerField(null=True, blank=True)  # 0–100
    # Symptoms (1–10)
    acne_level = models.PositiveSmallIntegerField(null=True, blank=True)
    fatigue_level = models.PositiveSmallIntegerField(null=True, blank=True)
    bloating_level = models.PositiveSmallIntegerField(null=True, blank=True)
    sleep_quality = models.PositiveSmallIntegerField(null=True, blank=True)
    # Graph
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    mood = models.PositiveSmallIntegerField(null=True, blank=True)  # 1–10

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_date'),
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} – {self.date}"


class DietDayLog(models.Model):
    """
    One row per user per date. Stores only the AI-generated diet plan: plan JSON, note, and checked slots.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diet_day_logs',
    )
    date = models.DateField(db_index=True)
    plan = models.JSONField(null=True, blank=True, help_text='AI plan: { "day": str, "slots": [...] }')
    note = models.TextField(blank=True)
    checked = models.JSONField(default=list, help_text='List of bools, one per slot')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_user_diet_date'),
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} diet – {self.date}"


class NotificationPreference(models.Model):
    """Per-user email notification toggles. One row per user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preference',
    )
    events_workshops = models.BooleanField(
        default=True,
        help_text='Events & Workshops notifications',
    )
    health_tips = models.BooleanField(
        default=True,
        help_text='Health Tips notifications',
    )
    app_updates = models.BooleanField(
        default=True,
        help_text='App Updates notifications',
    )
    breakfast_reminder = models.BooleanField(
        default=True,
        help_text='Breakfast reminder (scheduled email)',
    )
    water_reminder = models.BooleanField(
        default=True,
        help_text='Water reminder (scheduled email)',
    )
    stretch_reminder = models.BooleanField(
        default=True,
        help_text='Stretch reminder (scheduled email)',
    )
    daily_log_reminder = models.BooleanField(
        default=True,
        help_text='Daily log reminder – remind to enter today\'s log',
    )

    class Meta:
        verbose_name = 'Notification preference'
        verbose_name_plural = 'Notification preferences'

    def __str__(self):
        return f"Notifications for {self.user.username}"


class ReminderLog(models.Model):
    """Tracks which reminders were already sent today so we don't send twice."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reminder_logs',
    )
    date = models.DateField(db_index=True)
    reminder_type = models.CharField(max_length=32, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'date', 'reminder_type'], name='unique_user_date_reminder'),
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} – {self.date} – {self.reminder_type}"
