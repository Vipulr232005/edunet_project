"""
Management command: send scheduled reminder emails to users who have them enabled.
Run periodically via cron or Task Scheduler (e.g. every 15 min).

Schedule (hours in server timezone, default UTC):
- 8:00  → breakfast_reminder
- 10:00, 14:00, 16:00 → water_reminder
- 11:00 → stretch_reminder
- 20:00 → daily_log_reminder

Each reminder is sent at most once per user per day (ReminderLog).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from tracker.models import NotificationPreference, ReminderLog
from tracker.views import send_notification_email


# Playful, Zomato-style content for each reminder type
REMINDER_CONTENT = {
    'breakfast_reminder': {
        'subject': "Hey you 👀 Time to fuel up!",
        'body': (
            "Your body was thinking about you this morning…\n\n"
            "Slow days are still progress 💗 Grab something good for breakfast — "
            "you're doing fine, and we're here for it 🌸\n\n"
            "— PCOD GirlCare"
        ),
    },
    'water_reminder': {
        'subject': "Hydration check 💧",
        'body': (
            "Hey you 👀\n\n"
            "Your body was thinking about you… Drink a glass of water, stretch a little, "
            "and don't forget — you're doing fine 🌸\n\n"
            "— PCOD GirlCare"
        ),
    },
    'stretch_reminder': {
        'subject': "Stretch break? You deserve it 💗",
        'body': (
            "Hey you 👀\n\n"
            "Your body was thinking about you today… Take a minute to stretch — "
            "slow days are still progress 💗\n\n"
            "— PCOD GirlCare"
        ),
    },
    'daily_log_reminder': {
        'subject': "Don't forget to log today 🌸",
        'body': (
            "Hey you 👀\n\n"
            "Mood, steps, tiny wins — we're here for it. "
            "Log today's check-in when you get a sec 💗 You're doing fine.\n\n"
            "— PCOD GirlCare"
        ),
    },
}

# Which hour(s) (in server timezone) trigger which reminder. One reminder type can have multiple hours.
SCHEDULE = {
    8: ['breakfast_reminder'],
    10: ['water_reminder'],
    11: ['stretch_reminder'],
    14: ['water_reminder'],
    16: ['water_reminder'],
    20: ['daily_log_reminder'],
}


class Command(BaseCommand):
    help = 'Send scheduled reminder emails (breakfast, water, stretch, daily log) to users who have them enabled.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be sent without sending or logging.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        today = timezone.localdate()
        hour = now.hour

        reminder_types = SCHEDULE.get(hour, [])
        if not reminder_types:
            if not dry_run:
                self.stdout.write(self.style.NOTICE(f'No reminders scheduled for hour {hour} (server time).'))
            return

        User = get_user_model()
        sent = 0
        for reminder_type in reminder_types:
            if reminder_type not in REMINDER_CONTENT:
                continue
            content = REMINDER_CONTENT[reminder_type]
            # Users who have this reminder enabled and have an email
            prefs_qs = NotificationPreference.objects.filter(
                **{reminder_type: True}
            ).select_related('user')
            for prefs in prefs_qs:
                user = prefs.user
                email = (getattr(user, 'email', None) or '').strip()
                if not email:
                    continue
                # Already sent this reminder today?
                if ReminderLog.objects.filter(user=user, date=today, reminder_type=reminder_type).exists():
                    continue
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f'[dry-run] Would send {reminder_type} to {email}')
                    )
                    sent += 1
                    continue
                try:
                    n = send_notification_email(
                        user, reminder_type,
                        content['subject'], content['body'],
                    )
                    if n:
                        ReminderLog.objects.get_or_create(
                            user=user, date=today, reminder_type=reminder_type,
                        )
                        sent += 1
                        self.stdout.write(self.style.SUCCESS(f'Sent {reminder_type} to {email}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to send {reminder_type} to {email}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Done. Sent (or would send) {sent} reminder(s).'))
