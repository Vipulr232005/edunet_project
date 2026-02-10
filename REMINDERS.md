# Scheduled email reminders

Reminders (breakfast, water, stretch, daily log) are sent only to users who have them enabled in **Notification settings**, and only to each user's own email (`user.email`). No emails are hardcoded.

## Schedule (server timezone, default UTC)

| Time (hour) | Reminder        |
|-------------|-----------------|
| 8:00        | Breakfast       |
| 10:00       | Water           |
| 11:00       | Stretch         |
| 14:00       | Water           |
| 16:00       | Water           |
| 20:00       | Daily log       |

Each reminder is sent **at most once per user per day** (tracked in `ReminderLog`).

## Run the command

From the project root (`edunet_project/`):

```bash
python manage.py send_reminders
```

Test without sending:

```bash
python manage.py send_reminders --dry-run
```

## Schedule the command (run every 15–60 minutes)

### Linux / macOS (cron)

Edit crontab: `crontab -e`

Run every 15 minutes:

```
*/15 * * * *  cd /full/path/to/edunet_project && python manage.py send_reminders
```

Run every hour (on the hour):

```
0 * * * *  cd /full/path/to/edunet_project && python manage.py send_reminders
```

Use the **full path** to your project and the same Python that runs Django (e.g. from your venv).

### Windows (Task Scheduler)

1. Open **Task Scheduler**.
2. Create Basic Task → name e.g. "PCOD send reminders" → Daily (or at logon).
3. Action: **Start a program**
   - Program: `C:\Path\To\python.exe` (your Python executable, e.g. from Anaconda or venv)
   - Arguments: `manage.py send_reminders`
   - Start in: `C:\Users\Dell\Desktop\EDU\edunet_project`
4. In the task properties, set **Repeat task every** 15 minutes (or 1 hour) for a duration of 1 day (or indefinitely), so the command runs every interval.

Alternatively create a batch file that runs `python manage.py send_reminders` and point Task Scheduler at that script.

## Timezone

Reminder times use Django’s `timezone.now()` (server time). By default `TIME_ZONE` in `config/settings.py` is `'UTC'`. To use your local time (e.g. India):

1. Set `TIME_ZONE = 'Asia/Kolkata'` (or your zone) in `config/settings.py`.
2. Ensure `USE_TZ = True` (default).

Then 8:00 means 8:00 in that timezone.
