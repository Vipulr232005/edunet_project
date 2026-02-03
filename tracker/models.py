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
