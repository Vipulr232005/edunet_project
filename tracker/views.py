import json
import random
import re
import urllib.request
import urllib.error
import logging
from datetime import timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from .forms import SignUpForm, DailyLogForm, NotificationPreferenceForm
from .models import DailyLog, DietDayLog, NotificationPreference

logger = logging.getLogger(__name__)

MOTIVATIONS = [
    "Today, you choose foods that help your hormones feel safe and supported.",
    "Eating healthy today is an act of self-respect, not restriction.",
    "Your body is working hard for you—nourish it kindly.",
    "One healthy choice today can ease inflammation tomorrow.",
    "You don't need junk food to cope; you deserve real nourishment.",
    "Stable blood sugar = better mood, better energy, better you.",
    "You are not \"missing out\" by skipping junk—you're leveling up.",
    "Healing PCOD starts with small, loving daily decisions.",
    "Food is information—today, send your body calm, balanced signals.",
    "Your future self will thank you for today's discipline.",
    "Healthy eating today supports clearer skin, calmer cycles, and confidence.",
    "You deserve meals that fuel you, not drain you.",
    "Cravings pass, but self-care builds strength that lasts.",
    "You are choosing progress over momentary pleasure.",
    "Eating well today is a vote for hormone balance.",
    "You're allowed to prioritize your health without guilt.",
    "Junk food doesn't love you back—real food does.",
    "Your body is not the enemy; it's asking for support.",
    "Today's choices can reduce bloating, fatigue, and brain fog.",
    "You're not \"being strict\"—you're being intentional.",
    "Each healthy meal is a step toward cycle regularity.",
    "You are allowed to say no to food that harms you.",
    "Healing isn't instant, but consistency is powerful.",
    "You're choosing energy over exhaustion.",
    "Nourishing food helps your hormones feel less chaotic.",
    "You are doing this for balance, not perfection.",
    "Eating well today is a form of self-love.",
    "You don't need junk food to reward yourself—rest and care work better.",
    "Your body responds beautifully when treated gently.",
    "You are stronger than a craving.",
    "A healthy day today supports better sleep tonight.",
    "Every nourishing bite helps reduce insulin resistance.",
    "You are building a lifestyle, not chasing quick fixes.",
    "Choosing whole foods today supports long-term fertility and health.",
    "You deserve to feel light, energized, and confident.",
    "PCOD does not define you—but your care can transform it.",
    "One day of mindful eating is a powerful reset.",
    "You are allowed to protect your health fiercely.",
    "Healthy food is not punishment—it's medicine.",
    "Your hormones thrive on consistency, not chaos.",
    "You're choosing patience over impulse today.",
    "This is you showing up for your body.",
    "You don't owe junk food a yes.",
    "Every healthy choice is proof that you care about yourself.",
    "You are worthy of feeling good in your body.",
    "Food that nourishes you helps your mind feel calmer too.",
    "Today is about progress, not pressure.",
    "You're healing from the inside out.",
    "Skipping junk today is choosing peace over spikes and crashes.",
    "Take care of yourself today—you deserve a healthy, gentle life. 💚",
]

# Daily PCOD myth questions – BASIC and HARD
DAILY_MYTH_QUESTIONS_BASIC = [
    {
        "text": "PCOD only affects women who are overweight.",
        "fact": "False. PCOD can affect women of all body types. Weight can influence symptoms, but it is not the only cause.",
        "answer": False,
    },
    {
        "text": "Having PCOD means you can never get pregnant.",
        "fact": "False. Many women with PCOD conceive naturally or with support. PCOD can make things slower, not impossible.",
        "answer": False,
    },
    {
        "text": "PCOD is the same as PCOS.",
        "fact": "Not exactly. The terms are often used together, but PCOD usually refers to ovarian changes, while PCOS is a wider metabolic-hormonal picture.",
        "answer": False,
    },
    {
        "text": "Skipping periods with PCOD is always dangerous.",
        "fact": "Not always. Irregular cycles are a symptom that needs monitoring, but every skipped period is not an emergency. Regular check‑ins with your doctor help.",
        "answer": False,
    },
    {
        "text": "Only hormonal tablets can manage PCOD.",
        "fact": "False. Lifestyle, sleep, stress care, movement and nutrition often play a huge role alongside medicines.",
        "answer": False,
    },
    {
        "text": "PCOD means you did something wrong to your body.",
        "fact": "Absolutely not. PCOD is a mix of genetics, hormones, and environment. You deserve kindness, not blame.",
        "answer": False,
    },
]

DAILY_MYTH_QUESTIONS_HARD = [
    {
        "text": "If your periods look regular, your PCOD is fully cured.",
        "fact": "Not always. Regular periods are a good sign, but PCOD is about hormones, insulin, ovaries and metabolism together. Long‑term habits still matter.",
        "answer": False,
    },
    {
        "text": "PCOD happens only because of a ‘bad’ lifestyle.",
        "fact": "False. Lifestyle can worsen or ease symptoms, but genetics, hormones and environment are big players too. It is not a punishment.",
        "answer": False,
    },
    {
        "text": "If ultrasound shows cysts once, you will always have them.",
        "fact": "No. Ovarian appearance can change over time. Cysts may reduce as hormones, weight, and insulin resistance improve.",
        "answer": False,
    },
    {
        "text": "Carbs must be completely eliminated if you have PCOD.",
        "fact": "False. You don’t have to remove carbs, just choose smarter portions and fibre‑rich options. Balance beats extremes.",
        "answer": False,
    },
    {
        "text": "PCOD automatically goes away after marriage or pregnancy.",
        "fact": "Myth. Marriage or pregnancy are not treatments. Hormonal patterns can shift, but PCOD still needs gentle, long‑term care.",
        "answer": False,
    },
    {
        "text": "If you are thin with PCOD, you don’t need to worry.",
        "fact": "Lean PCOD is real. Even at a lower weight, hormones and insulin may still need support and monitoring.",
        "answer": False,
    },
]


def get_daily_myth_questions():
    """Return today's BASIC and HARD myth questions based purely on the date."""
    today = timezone.localdate()
    # Day of year (1–366) – safe for indexing
    day_of_year = today.timetuple().tm_yday
    basic_index = day_of_year % len(DAILY_MYTH_QUESTIONS_BASIC)
    hard_index = day_of_year % len(DAILY_MYTH_QUESTIONS_HARD)
    return DAILY_MYTH_QUESTIONS_BASIC[basic_index], DAILY_MYTH_QUESTIONS_HARD[hard_index]
# Playful, Zomato-style email content for notifications (use as samples or override per type)
SAMPLE_EMAIL_EVENTS_WORKSHOPS = (
    "Hey you 👀\n\n"
    "We've got something fun coming up — events & workshops just for you.\n\n"
    "Your body was thinking about you today… Slow days are still progress 💗\n"
    "Come say hi, learn something new, and don't forget — you're doing fine 🌸\n\n"
    "— PCOD GirlCare"
)
SAMPLE_EMAIL_HEALTH_TIPS = (
    "Hey you 👀\n\n"
    "Your body was thinking about you today…\n\n"
    "Slow days are still progress 💗 Drink some water, stretch a little, "
    "and don't forget — you're doing fine 🌸\n\n"
    "— PCOD GirlCare"
)
SAMPLE_EMAIL_APP_UPDATES = (
    "Hey you 👀\n\n"
    "We've been cooking something new for you — a little app update to make your journey smoother.\n\n"
    "Check it out when you can. No rush — we'll be here 💗\n\n"
    "— PCOD GirlCare"
)


def home(request):
    """Landing / info page – shown to everyone (logged in or not)."""
    return render(request, 'tracker/home.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('tracker:home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tracker:login')
    else:
        form = SignUpForm()
    return render(request, 'tracker/signup.html', {'form': form})


@login_required
@ensure_csrf_cookie
def dashboard(request):
    user = request.user
    today = timezone.localdate()

    # Daily myth questions (same for everyone on a given day)
    daily_basic_myth, daily_hard_myth = get_daily_myth_questions()

    # Only this user's data – secured
    today_log = DailyLog.objects.filter(user=user, date=today).first()
    last_7 = (
        DailyLog.objects.filter(user=user)
        .filter(date__lte=today)
        .order_by('-date')[:7]
    )
    last_7_list = list(last_7)
    last_7_list.reverse()  # oldest first for chart

    # Build chart data from current user only (for JS)
    chart_labels = []
    chart_weight = []
    chart_mood = []
    for log in last_7_list:
        chart_labels.append(log.date.strftime('%a'))
        chart_weight.append(float(log.weight_kg) if log.weight_kg is not None else None)
        chart_mood.append(log.mood if log.mood is not None else None)
    chart_labels_json = json.dumps(chart_labels)
    chart_weight_json = json.dumps(chart_weight)
    chart_mood_json = json.dumps(chart_mood)

    # Defaults when no log today
    def default(val, d):
        return val if val is not None else d

    # Show the motivation popup only once per login/session.
    # We store a flag in the Django session so that after the first
    # successful render of the dashboard, the popup is not shown again
    # until the user logs out (which clears the session).
    show_motivation = not request.session.get('motivation_shown', False)
    if show_motivation:
        request.session['motivation_shown'] = True

    if today_log:
        symptoms_count = sum(1 for x in [
            today_log.acne_level, today_log.fatigue_level,
            today_log.bloating_level, today_log.sleep_quality
        ] if x is not None)
        if symptoms_count == 0:
            symptoms_count = 1
        context = {
            'username': user.username,
            'show_motivation': show_motivation,
            'daily_motivation': random.choice(MOTIVATIONS),
            'daily_basic_myth': daily_basic_myth,
            'daily_hard_myth': daily_hard_myth,
            'today_log': today_log,
            'log_form': DailyLogForm(instance=today_log),
            'symptoms_count': symptoms_count,
            'acne_level': default(today_log.acne_level, 0),
            'fatigue_level': default(today_log.fatigue_level, 0),
            'bloating_level': default(today_log.bloating_level, 0),
            'sleep_quality': default(today_log.sleep_quality, 0),
            'cycle_day': default(today_log.cycle_day, 0),
            'steps': default(today_log.steps, 0),
            'water_glasses': default(today_log.water_glasses, 0),
            'wellness_score': default(today_log.wellness_score, 0),
            'chart_labels': chart_labels,
            'chart_weight': chart_weight,
            'chart_mood': chart_mood,
            'chart_labels_json': chart_labels_json,
            'chart_weight_json': chart_weight_json,
            'chart_mood_json': chart_mood_json,
            'has_chart_data': any(w is not None for w in chart_weight) or any(m is not None for m in chart_mood),
        }
    else:
        context = {
            'username': user.username,
            'show_motivation': show_motivation,
            'daily_motivation': random.choice(MOTIVATIONS),
            'daily_basic_myth': daily_basic_myth,
            'daily_hard_myth': daily_hard_myth,
            'today_log': None,
            'log_form': DailyLogForm(),
            'symptoms_count': 0,
            'acne_level': None,
            'fatigue_level': None,
            'bloating_level': None,
            'sleep_quality': None,
            'cycle_day': None,
            'steps': None,
            'water_glasses': None,
            'wellness_score': None,
            'chart_labels': chart_labels,
            'chart_weight': chart_weight,
            'chart_mood': chart_mood,
            'chart_labels_json': chart_labels_json,
            'chart_weight_json': chart_weight_json,
            'chart_mood_json': chart_mood_json,
            'has_chart_data': any(w is not None for w in chart_weight) or any(m is not None for m in chart_mood),
        }

    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'daily_log':
            form = DailyLogForm(request.POST, instance=today_log)
            if form.is_valid():
                log = form.save(commit=False)
                log.user = user
                log.date = today
                log.save()
                return redirect('tracker:dashboard')
            context['log_form'] = form
        elif form_type == 'quick_water':
            glasses = request.POST.get('water_glasses')
            try:
                n = max(0, min(20, int(glasses or 0)))
                if today_log:
                    today_log.water_glasses = n
                    today_log.save(update_fields=['water_glasses'])
                else:
                    DailyLog.objects.create(user=user, date=today, water_glasses=n)
                return redirect('tracker:dashboard')
            except (ValueError, TypeError):
                pass

    return render(request, 'tracker/dashboard.html', context)


@login_required
def cycle_tracker(request):
    """Cycle tracker page – cycle day, phase, recent logs."""
    user = request.user
    today = timezone.localdate()
    today_log = DailyLog.objects.filter(user=user, date=today).first()
    cycle_day = today_log.cycle_day if today_log else None
    # Last 30 days with cycle_day for trend
    recent = (
        DailyLog.objects.filter(user=user, cycle_day__isnull=False)
        .exclude(cycle_day=0)
        .order_by('-date')[:30]
    )
    # Phase info (typical 28-day: menstrual 1-5, follicular 6-13, ovulatory 14-16, luteal 17-28)
    phase = None
    if cycle_day is not None and cycle_day > 0:
        if cycle_day <= 5:
            phase = ('Menstrual', 'Rest, gentle movement, iron-rich foods.')
        elif cycle_day <= 13:
            phase = ('Follicular', 'Energy often rises—good time for exercise and new habits.')
        elif cycle_day <= 16:
            phase = ('Ovulatory', 'Peak energy; focus on strength and social connection.')
        else:
            phase = ('Luteal', 'Listen to your body; prioritize sleep and nourishment.')
    context = {
        'username': user.username,
        'cycle_day': cycle_day,
        'phase': phase,
        'recent_logs': recent,
        'today_log': today_log,
    }
    return render(request, 'tracker/cycle_tracker.html', context)


@login_required
def wellness(request):
    """Wellness page – score, sleep, mood, tips."""
    user = request.user
    today = timezone.localdate()
    today_log = DailyLog.objects.filter(user=user, date=today).first()
    last_7 = (
        DailyLog.objects.filter(user=user, date__lte=today)
        .order_by('-date')[:7]
    )
    wellness_score = today_log.wellness_score if today_log else None
    sleep_quality = today_log.sleep_quality if today_log else None
    mood = today_log.mood if today_log else None
    mood_label = _mood_label_for_agent(mood)
    wellness_days = [
        {'date': log.date, 'wellness': log.wellness_score, 'mood': log.mood, 'sleep': log.sleep_quality}
        for log in last_7
    ]
    context = {
        'username': user.username,
        'wellness_score': wellness_score,
        'sleep_quality': sleep_quality,
        'mood': mood,
        'mood_label': mood_label,
        'wellness_days': wellness_days,
        'gemini_configured': bool(getattr(settings, 'GEMINI_API_KEY', '').strip()),
    }
    return render(request, 'tracker/wellness.html', context)


@login_required
def insights(request):
    """Insights page – trends, symptom summary, charts."""
    user = request.user
    today = timezone.localdate()
    last_14 = (
        DailyLog.objects.filter(user=user, date__lte=today)
        .order_by('-date')[:14]
    )
    last_14_list = list(last_14)
    last_14_list.reverse()
    # Chart data
    chart_labels = [log.date.strftime('%d %b') for log in last_14_list]
    chart_weight = [float(log.weight_kg) if log.weight_kg else None for log in last_14_list]
    chart_mood = [log.mood if log.mood is not None else None for log in last_14_list]
    chart_wellness = [log.wellness_score if log.wellness_score is not None else None for log in last_14_list]
    # Averages (last 7 with data)
    last_7 = last_14_list[-7:] if len(last_14_list) >= 7 else last_14_list
    def avg(values): v = [x for x in values if x is not None]; return sum(v) / len(v) if v else None
    avg_mood = avg([log.mood for log in last_7])
    avg_wellness = avg([log.wellness_score for log in last_7])
    avg_acne = avg([log.acne_level for log in last_7])
    avg_fatigue = avg([log.fatigue_level for log in last_7])
    log_count = len(last_14_list)
    context = {
        'username': user.username,
        'chart_labels': chart_labels,
        'chart_weight': chart_weight,
        'chart_mood': chart_mood,
        'chart_wellness': chart_wellness,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_weight_json': json.dumps(chart_weight),
        'chart_mood_json': json.dumps(chart_mood),
        'chart_wellness_json': json.dumps(chart_wellness),
        'avg_mood': round(avg_mood, 1) if avg_mood is not None else None,
        'avg_wellness': round(avg_wellness, 1) if avg_wellness is not None else None,
        'avg_acne': round(avg_acne, 1) if avg_acne is not None else None,
        'avg_fatigue': round(avg_fatigue, 1) if avg_fatigue is not None else None,
        'log_count': log_count,
    }
    return render(request, 'tracker/insights.html', context)


# Diet plan: 7 days (Monday=Day1 .. Sunday=Day7). Each day has 7 slots.
# Approximate macros per slot (protein_g, carbs_g, kcal) for chart.
DIET_SLOT_MACROS = {
    'early_morning': (5, 3, 80),
    'breakfast': (18, 35, 380),
    'mid_morning': (1, 5, 30),
    'lunch': (35, 45, 520),
    'evening_snack': (0.5, 15, 70),
    'dinner': (30, 40, 450),
    'bedtime': (0, 0, 5),
}

DIET_PLAN = [
    # Day 1 (Monday)
    [
        {'slot': 'early_morning', 'label': '07:00 AM – Early Morning', 'foods': 'Detox drink, Almonds (6–8), Walnuts (3–4)'},
        {'slot': 'breakfast', 'label': '08:30 AM – Breakfast', 'foods': 'Moong dal cheela (2)'},
        {'slot': 'mid_morning', 'label': '10:30 AM – Mid-Morning', 'foods': 'Detox drink, Cucumber (1) / Carrot (1)'},
        {'slot': 'lunch', 'label': '01:00 PM – Lunch', 'foods': 'Chapati (2), Chicken gravy (150 g), Vegetables, Curd'},
        {'slot': 'evening_snack', 'label': '04:00 PM – Evening Snack', 'foods': 'Detox drink, 1 fruit (apple / orange / watermelon / guava)'},
        {'slot': 'dinner', 'label': '07:00 PM – Dinner', 'foods': 'Sprout salad, Ragi dosa (2), Grilled chicken (100 g)'},
        {'slot': 'bedtime', 'label': '08:00 PM – Bedtime', 'foods': 'Cinnamon water'},
    ],
    # Day 2 (Tuesday)
    [
        {'slot': 'early_morning', 'label': '07:00 AM', 'foods': 'Detox drink, Almonds (6–8), Walnuts (3–4)'},
        {'slot': 'breakfast', 'label': '08:30 AM', 'foods': 'Wheat roti (2), Dal curry, Egg whites (2)'},
        {'slot': 'mid_morning', 'label': '10:30 AM', 'foods': 'Detox drink, Cucumber (1) / Carrot (1)'},
        {'slot': 'lunch', 'label': '01:00 PM', 'foods': 'Brown rice (6 tbsp), Sambar, Kidney beans curry (50 g), Steamed chicken breast (150 g), Cucumber salad (½ cup)'},
        {'slot': 'evening_snack', 'label': '04:00 PM', 'foods': 'Detox drink, 1 fruit'},
        {'slot': 'dinner', 'label': '07:00 PM', 'foods': 'Chicken sweet corn soup (1 bowl)'},
        {'slot': 'bedtime', 'label': '08:00 PM', 'foods': 'Cinnamon water'},
    ],
    # Day 3 (Wednesday)
    [
        {'slot': 'early_morning', 'label': '07:00 AM', 'foods': 'Detox drink, Almonds (6–8), Walnuts (3–4)'},
        {'slot': 'breakfast', 'label': '08:30 AM', 'foods': 'Paneer stuffed roti (2), Egg white (2)'},
        {'slot': 'mid_morning', 'label': '10:30 AM', 'foods': 'Detox drink, Cucumber (1) / Carrot (1)'},
        {'slot': 'lunch', 'label': '01:00 PM', 'foods': 'Brown rice (6 tbsp), Grilled paneer (150 g), Bhindi masala, Curd'},
        {'slot': 'evening_snack', 'label': '04:00 PM', 'foods': 'Detox drink, 1 fruit'},
        {'slot': 'dinner', 'label': '07:00 PM', 'foods': 'Ragi dosa (2), Paneer bhurji (150 g)'},
        {'slot': 'bedtime', 'label': '08:00 PM', 'foods': 'Cinnamon water'},
    ],
    # Day 4 (Thursday)
    [
        {'slot': 'early_morning', 'label': '07:00 AM', 'foods': 'Detox drink, Almonds (6–8), Walnuts (3–4)'},
        {'slot': 'breakfast', 'label': '08:30 AM', 'foods': 'Chapati (2), Green peas curry (½ cup), 1 egg + 1 egg white'},
        {'slot': 'mid_morning', 'label': '10:30 AM', 'foods': 'Detox drink, Cucumber (1) / Carrot (1)'},
        {'slot': 'lunch', 'label': '01:00 PM', 'foods': 'Chapati (2), Egg bhurji (150 g), Vegetable salad, Curd'},
        {'slot': 'evening_snack', 'label': '04:00 PM', 'foods': 'Detox drink, 1 fruit'},
        {'slot': 'dinner', 'label': '07:00 PM', 'foods': 'Palak dosa (1), Egg bhurji, Vegetables'},
        {'slot': 'bedtime', 'label': '08:00 PM', 'foods': 'Cinnamon water'},
    ],
    # Day 5 (Friday)
    [
        {'slot': 'early_morning', 'label': '07:00 AM', 'foods': 'Detox drink, Almonds (6–8), Walnuts (3–4)'},
        {'slot': 'breakfast', 'label': '08:30 AM', 'foods': 'Wheat cheela / Wheat roti (2), Cowpea curry, Egg white (2)'},
        {'slot': 'mid_morning', 'label': '10:30 AM', 'foods': 'Detox drink, Cucumber (1) / Carrot (1)'},
        {'slot': 'lunch', 'label': '01:00 PM', 'foods': 'Veg pulav rice (6 tbsp), Soya chunk curry (100 g), Chicken roast (150 g), Curd'},
        {'slot': 'evening_snack', 'label': '04:00 PM', 'foods': 'Detox drink, 1 fruit'},
        {'slot': 'dinner', 'label': '07:00 PM', 'foods': 'Boiled black channa (½ cup), Tomato & coriander, Chapati (1), Dal curry'},
        {'slot': 'bedtime', 'label': '08:00 PM', 'foods': 'Cinnamon water'},
    ],
    # Day 6 (Saturday)
    [
        {'slot': 'early_morning', 'label': '07:00 AM', 'foods': 'Detox drink, Almonds (6–8), Walnuts (3–4)'},
        {'slot': 'breakfast', 'label': '08:30 AM', 'foods': 'Overnight oats, Seeds (pumpkin + sunflower + flaxseed), Egg whites (2)'},
        {'slot': 'mid_morning', 'label': '10:30 AM', 'foods': 'Detox drink, Cucumber (1) / Carrot (1)'},
        {'slot': 'lunch', 'label': '01:00 PM', 'foods': 'Brown rice (6 tbsp), Grilled paneer (150 g), Bhindi masala, Curd'},
        {'slot': 'evening_snack', 'label': '04:00 PM', 'foods': 'Detox drink, 1 fruit'},
        {'slot': 'dinner', 'label': '07:00 PM', 'foods': 'Wheat dosa (2), Chicken / Fish (150 g), Salad'},
        {'slot': 'bedtime', 'label': '08:00 PM', 'foods': 'Cinnamon water'},
    ],
    # Day 7 (Sunday)
    [
        {'slot': 'early_morning', 'label': '07:00 AM', 'foods': 'Detox drink, Almonds (6–8), Walnuts (3–4)'},
        {'slot': 'breakfast', 'label': '08:30 AM', 'foods': 'Moong dal cheela (2)'},
        {'slot': 'mid_morning', 'label': '10:30 AM', 'foods': 'Detox drink, Cucumber (1) / Carrot (1)'},
        {'slot': 'lunch', 'label': '01:00 PM', 'foods': 'Brown rice (6 tbsp), Chicken (150 g), Soya bhurji, Curd'},
        {'slot': 'evening_snack', 'label': '04:00 PM', 'foods': 'Detox drink, 1 fruit'},
        {'slot': 'dinner', 'label': '07:00 PM', 'foods': "Roti / Chapati (2), Lady's finger sabji, Paneer gravy (150 g)"},
        {'slot': 'bedtime', 'label': '08:00 PM', 'foods': 'Cinnamon water'},
    ],
]

WEEKDAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def send_notification_email(user, notification_type, subject, body_plain):
    """
    Send an email ONLY to the given user's email (user.email). No hardcoded addresses.
    Use send_notification_if_enabled() to respect user preferences.
    """
    email = getattr(user, 'email', None) or ''
    if not email or not email.strip():
        return 0
    try:
        return send_mail(
            subject=subject,
            message=body_plain,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[email.strip()],
            fail_silently=False,
        )
    except Exception:
        return 0


def send_notification_if_enabled(user, notification_type, subject, body_plain):
    """
    Send email to user only if they have enabled this notification type.
    notification_type: one of 'events_workshops', 'health_tips', 'app_updates',
    'breakfast_reminder', 'water_reminder', 'stretch_reminder', 'daily_log_reminder'
    """
    prefs = NotificationPreference.objects.filter(user=user).first()
    if not prefs:
        return 0
    if notification_type == 'events_workshops' and not prefs.events_workshops:
        return 0
    if notification_type == 'health_tips' and not prefs.health_tips:
        return 0
    if notification_type == 'app_updates' and not prefs.app_updates:
        return 0
    if notification_type == 'breakfast_reminder' and not prefs.breakfast_reminder:
        return 0
    if notification_type == 'water_reminder' and not prefs.water_reminder:
        return 0
    if notification_type == 'stretch_reminder' and not prefs.stretch_reminder:
        return 0
    if notification_type == 'daily_log_reminder' and not prefs.daily_log_reminder:
        return 0
    return send_notification_email(user, notification_type, subject, body_plain)


# --- AI Diet Agent (Gemini API) ---

# Mode guard at top of each prompt to avoid cross-mode behavior.
SYSTEM_SUPPORT_PROMPT_BASE = (
    "You are in PCOD Support Chat mode. Do NOT generate meal plans, calorie counts, or structured JSON.\n"
    "You are a gentle, empathetic support companion for someone managing PCOD (PCOS).\n\n"
    "PRIMARY GOAL:\n"
    "- Help the user feel heard, validated, and gently supported.\n"
    "- Prioritize emotional acknowledgment BEFORE explanations.\n\n"
    "STYLE & TONE RULES:\n"
    "- Never assume the user feels good just because wellness scores are high.\n"
    "- Reflect the user's concern in the first 1–2 sentences (e.g., discomfort, confusion, worry).\n"
    "- Use warm, human language — not dashboard summaries or motivational slogans.\n"
    "- Avoid cheerleading, toxic positivity, or dismissive reassurance.\n\n"
    "CONTENT RULES:\n"
    "- Do NOT diagnose or give medical treatment.\n"
    "- Normalize PCOD-related experiences without minimizing discomfort.\n"
    "- When relevant, gently connect symptoms to cycle day, hormones, digestion, stress, or hydration.\n"
    "- Offer 2–4 simple, optional self-care ideas (hydration, movement, food awareness, rest).\n"
    "- Use bullets for clarity when listing causes or tips.\n\n"
    "SAFETY:\n"
    "- Do not cause alarm.\n"
    "- Suggest seeing a doctor ONLY if symptoms are severe, persistent, or worsening.\n\n"
    "WELLNESS CONTEXT:\n"
    "- Use wellness context only as background. Do NOT praise or judge the user based on it.\n\n"
    "OUTPUT FORMAT:\n"
    "- Short paragraphs.\n"
    "- Bullets for causes or tips.\n"
    "- No emojis.\n"
    "- No diet plans, calorie counts, or structured data.\n"
)

SYSTEM_DIET_PROMPT_BASE = (
    "You are in AI Diet Planner mode. Only answer with diet guidance or structured diet JSON when requested. Do NOT provide emotional counseling. "
    "You are a supportive, friendly diet and nutrition assistant for someone managing PCOD (PCOS). "
    "Do not give medical advice or diagnose. Suggest general wellness and diet ideas only. "
    "Keep replies concise and warm. "
    "Target intake: under 1800 kcal, 80-100 g protein when suggesting full day ideas. "
    "When the user clearly asks for a full-day diet plan (e.g. breakfast, lunch, snack, dinner with timings), ALWAYS, at the end of your reply, "
    "include a machine-readable JSON block between the markers ---DIET_PLAN_JSON_START--- and ---DIET_PLAN_JSON_END---. "
    "The JSON MUST have this exact shape: "
    "{"
    "\"day\": \"Monday\", "
    "\"slots\": ["
    "{"
    "\"time\": \"07:00\", "
    "\"label\": \"07:00 AM – Early Morning\", "
    "\"slot_key\": \"early_morning\", "
    "\"title\": \"Detox drink, Almonds, Walnuts\", "
    "\"description\": \"Detox drink, Almonds (6–8), Walnuts (3–4)\", "
    "\"protein_g\": 6, "
    "\"carbs_g\": 10, "
    "\"calories_kcal\": 120"
    "}"
    "]"
    "}. "
    "Use as many slots as needed for the day (e.g. early_morning, breakfast, mid_morning, lunch, evening_snack, dinner, bedtime). "
    "Return ONLY valid JSON matching this schema. Do not include explanations, markdown, or extra text inside the JSON block. "
    "You may still write a friendly explanation before the JSON, but the JSON part must be clean so it can be parsed by code."
)


def _build_wellness_ctx(user, for_support=False):
    """Build a bullet-format wellness context string from today's or latest DailyLog.
    When for_support=True, use a header that tells the model not to over-prioritize wellness data."""
    today = timezone.localdate()
    log = DailyLog.objects.filter(user=user, date=today).first()
    if not log:
        log = DailyLog.objects.filter(user=user).order_by("-date").first()
    bullets = []
    if log:
        mood_label = _mood_label_for_agent(log.mood)
        bullets.append("Mood: " + mood_label)
        if log.wellness_score is not None:
            bullets.append("Wellness score: " + str(log.wellness_score) + "%")
        if log.sleep_quality is not None:
            bullets.append("Sleep: " + str(log.sleep_quality) + "/10")
        if getattr(log, "steps", None) is not None:
            bullets.append("Steps: " + str(log.steps))
        if getattr(log, "water_glasses", None) is not None:
            bullets.append("Water: " + str(log.water_glasses) + " glasses")
        if getattr(log, "cycle_day", None) is not None:
            bullets.append("Cycle day: " + str(log.cycle_day))
    else:
        bullets.append("Mood: not logged today")
    header = (
        "User wellness context (use gently, do not over-prioritize):"
        if for_support
        else "User wellness context:"
    )
    return header + "\n- " + "\n- ".join(bullets)


def _mood_label_for_agent(mood_value):
    """Map mood 1–10 to a short label for the AI context."""
    if mood_value is None:
        return "not logged today"
    if mood_value <= 3:
        return "low / tired"
    if mood_value <= 5:
        return "stressed / okay"
    if mood_value >= 8:
        return "energetic / great"
    return "calm / moderate"


def _call_gemini(user_message, system_instruction, api_key, history=None, max_output_tokens=1024):
    """Call Gemini generateContent API. Returns (reply_text, error_message)."""
    if not api_key or not api_key.strip():
        logger.error("Gemini API key is missing or empty. Check GEMINI_API_KEY in environment/.env.")
        return None, "AI is not configured. Add GEMINI_API_KEY to your .env file."
    key = api_key.strip()
    # Use single-turn format: one user message with system context in the prompt (most reliable)
    prompt_parts = []
    if system_instruction:
        prompt_parts.append(system_instruction)
    if history:
        prompt_parts.append("\n\nRecent conversation:")
        for h in history[-6:]:
            who = "User" if h.get("role") == "user" else "Assistant"
            text = (h.get("content") or "").strip()
            if text:
                prompt_parts.append(f"\n{who}: {text}")
    prompt_parts.append("\n\nUser: " + user_message)
    prompt_parts.append("\n\nAssistant:")
    full_prompt = "".join(prompt_parts)
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_output_tokens},
    }
    body = json.dumps(payload).encode("utf-8")
    # Prefer Gemma 3 12B; fallback to Gemini Flash models (all v1beta)
    for model in (      "gemini-2.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            logger.debug("Calling Gemini model %s", model)
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            logger.debug("Gemini model %s responded successfully", model)
            for c in data.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    if "text" in p:
                        return p["text"].strip(), None
            logger.error("Gemini model %s returned no text candidates.", model)
            return None, "No reply from the model."
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                if e.fp:
                    err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            err_snippet = (err_body[:400] if err_body else str(e))
            logger.error(
                "Gemini HTTPError for model %s (status %s): %s",
                model,
                e.code,
                err_snippet,
            )
            if e.code == 404:
                continue
            return None, f"API error ({e.code}): {err_snippet}"
        except Exception as e:
            logger.exception("Error calling Gemini model %s: %s", model, e)
            return None, str(e)
    logger.error(
        "API error: no supported Gemini model responded successfully. "
        "Tried models: gemma-3-12b-it, gemini-3-flash-preview, gemini-2.5-flash, gemini-2.0-flash, gemini-1.5-flash."
    )
    return None, "API error: no supported model found. Try gemini-2.0-flash or gemini-1.5-flash in Google AI Studio."


@login_required
@ensure_csrf_cookie
def ai_diet_agent(request):
    """AI Diet Agent page: chat UI; mood from today's or latest log."""
    user = request.user
    today = timezone.localdate()
    today_log = DailyLog.objects.filter(user=user, date=today).first()
    if today_log:
        mood_val = today_log.mood
        mood_label = _mood_label_for_agent(mood_val)
        has_log_today = True
    else:
        latest = DailyLog.objects.filter(user=user).order_by("-date").first()
        mood_val = latest.mood if latest else None
        mood_label = _mood_label_for_agent(mood_val)
        has_log_today = False
    return render(request, "tracker/ai_diet_agent.html", {
        "username": user.username,
        "mood": mood_val,
        "mood_label": mood_label,
        "has_log_today": has_log_today,
        "gemini_configured": bool(getattr(settings, "GEMINI_API_KEY", "").strip()),
    })


@login_required
@require_http_methods(["POST"])
def pcod_support_chat(request):
    """POST: JSON { message: string, history?: [{role, content}] }. Returns { reply: string } or { error: string }."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    message = (body.get("message") or "").strip()
    if len(message) > 2000:
        return JsonResponse({"error": "Message too long."}, status=400)
    if not message:
        return JsonResponse({"error": "Empty message."}, status=400)
    history = body.get("history")
    if history is not None and not isinstance(history, list):
        history = None
    user = request.user
    wellness_ctx = _build_wellness_ctx(user, for_support=True)
    system_instruction = SYSTEM_SUPPORT_PROMPT_BASE + "\n\n" + wellness_ctx
    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    reply_text, err = _call_gemini(message, system_instruction, api_key, history)
    if err:
        return JsonResponse({"error": err}, status=503)
    return JsonResponse({"reply": reply_text})


@login_required
@require_http_methods(["POST"])
def diet_planner_chat(request):
    """POST: JSON { message: string, history?: [{role, content}] }. Returns { reply: string } or { error: string }."""
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    message = (body.get("message") or "").strip()
    if len(message) > 2000:
        return JsonResponse({"error": "Message too long."}, status=400)
    if not message:
        return JsonResponse({"error": "Empty message."}, status=400)
    history = body.get("history")
    if history is not None and not isinstance(history, list):
        history = None
    user = request.user
    wellness_ctx = _build_wellness_ctx(user)
    preference_parts = []
    last_user_text = (body.get("last_user_text") or "").strip()
    last_assistant_text = (body.get("last_assistant_text") or "").strip()
    if last_user_text:
        preference_parts.append("User's latest request/preference: " + last_user_text)
    if last_assistant_text:
        preference_parts.append("Assistant's last reply: " + last_assistant_text)
    preference_ctx = " ".join(preference_parts) if preference_parts else ""
    system_instruction = (
        SYSTEM_DIET_PROMPT_BASE + "\n\n" + wellness_ctx +
        " Consider mood, sleep and wellness when suggesting foods or habits. "
    )
    if preference_ctx:
        system_instruction += "\n\nStrictly respect when shaping the plan: " + preference_ctx
    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    reply_text, err = _call_gemini(message, system_instruction, api_key, history)
    if err:
        return JsonResponse({"error": err}, status=503)
    # If reply contains a diet plan JSON block, extract it and return for "Insert to my plan"
    reply_display = reply_text
    plan = None
    start_marker = "---DIET_PLAN_JSON_START---"
    end_marker = "---DIET_PLAN_JSON_END---"
    if start_marker in reply_text and end_marker in reply_text:
        try:
            start_idx = reply_text.index(start_marker) + len(start_marker)
            end_idx = reply_text.index(end_marker)
            json_str = reply_text[start_idx:end_idx].strip()
            plan = json.loads(json_str)
            if isinstance(plan, dict) and isinstance(plan.get("slots"), list) and plan["slots"]:
                for slot in plan["slots"]:
                    if isinstance(slot, dict):
                        slot.setdefault("protein_g", 0)
                        slot.setdefault("carbs_g", 0)
                        slot.setdefault("calories_kcal", 0)
                # Strip the JSON block from display
                reply_display = (
                    reply_text[: reply_text.index(start_marker)].strip() +
                    reply_text[reply_text.index(end_marker) + len(end_marker) :].strip()
                )
                reply_display = reply_display.strip()
            else:
                plan = None
        except (json.JSONDecodeError, ValueError):
            plan = None
    payload = {"reply": reply_display}
    if plan is not None:
        payload["plan"] = plan
    return JsonResponse(payload)


@login_required
@require_http_methods(["POST"])
def diet_plan_import(request):
    """
    Save an AI-generated diet plan to the database (called when user clicks "Insert this to my plan").
    Expects JSON: { "plan": { "day": str, "slots": [ {...}, ... ] }, optional "note": str }.
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    plan = body.get("plan")
    if not isinstance(plan, dict):
        return JsonResponse({"error": "Missing or invalid 'plan' object."}, status=400)
    slots = plan.get("slots")
    if not isinstance(slots, list) or not slots:
        return JsonResponse({"error": "Plan must contain a non-empty 'slots' list."}, status=400)
    # Minimal per-slot validation
    for idx, slot in enumerate(slots):
        if not isinstance(slot, dict):
            return JsonResponse({"error": f"Slot {idx} is not an object."}, status=400)
        if "time" not in slot or "label" not in slot or "description" not in slot:
            return JsonResponse({"error": f"Slot {idx} is missing required fields."}, status=400)
        slot.setdefault("protein_g", 0)
        slot.setdefault("carbs_g", 0)
        slot.setdefault("calories_kcal", 0)
    note = (body.get("note") or "").strip() if isinstance(body.get("note"), str) else ""
    today = timezone.localdate()
    checked = [False] * len(slots)
    DietDayLog.objects.update_or_create(
        user=request.user,
        date=today,
        defaults={"plan": plan, "note": note, "checked": checked},
    )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def diet_plan_generate(request):
    """
    Generate a fresh AI diet plan (JSON only) and return it. Does not store in session;
    user must click "Insert this to my plan" in the chat to save. Returns { "ok": True, "plan": plan }.
    """
    user = request.user
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        body = {}
    last_user_text = (body.get("last_user_text") or "").strip()
    last_assistant_text = (body.get("last_assistant_text") or "").strip()
    wellness_ctx = _build_wellness_ctx(user)
    preference_parts = []
    if last_user_text:
        preference_parts.append("User's latest request/preference: " + last_user_text)
    if last_assistant_text:
        preference_parts.append("Assistant's last reply: " + last_assistant_text)
    preference_ctx = " ".join(preference_parts) if preference_parts else ""

    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    system_instruction = (
        SYSTEM_DIET_PROMPT_BASE + "\n\n" + wellness_ctx + " "
        "For this specific request, you MUST respond with ONLY a single JSON object, "
        "no explanation, no extra text, no markdown formatting, no code blocks. "
        "Start directly with { and end with }. Use multiple slots for the full day. "
        "Adjust foods and macros for PCOD-friendly, balanced meals. "
    )
    if preference_ctx:
        system_instruction += "Strictly respect when shaping the plan: " + preference_ctx + " "
    system_instruction += (
        "CRITICAL: Return ONLY valid JSON starting with { and ending with }. "
        "Do not wrap in markdown code blocks. Do not add any text before or after the JSON."
    )
    # Simple message; full prompt is built inside _call_gemini
    # Use higher token limit so full diet plan JSON is not truncated
    message = "Generate today's full-day diet plan as JSON."
    reply_text, err = _call_gemini(
        message, system_instruction, api_key, history=None, max_output_tokens=8192
    )
    if err:
        return JsonResponse({"error": err}, status=503)
    # Try to extract the JSON object from the reply (model may add extra text or markdown)
    plan = None
    json_str = None
    
    # First, try to extract JSON from markdown code blocks (```json ... ```)
    json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', reply_text, re.DOTALL)
    if json_block_match:
        json_str = json_block_match.group(1)
        try:
            plan = json.loads(json_str)
        except json.JSONDecodeError:
            json_str = None
    
    # If no code block found, try to find JSON between first { and last }
    if json_str is None:
        try:
            json_start = reply_text.index("{")
            json_end = reply_text.rindex("}") + 1
            json_str = reply_text[json_start:json_end]
            plan = json.loads(json_str)
        except (ValueError, json.JSONDecodeError):
            # Try to find any JSON-like structure
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', reply_text, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    plan = json.loads(json_str)
                except json.JSONDecodeError:
                    pass
    
    if plan is None:
        return JsonResponse({
            "error": "Model did not return valid JSON. Response: " + reply_text[:200]
        }, status=502)
    # Reuse the same validation/storage logic as import
    if not isinstance(plan, dict):
        return JsonResponse({"error": "Returned plan is not a JSON object."}, status=502)
    slots = plan.get("slots")
    if not isinstance(slots, list) or not slots:
        return JsonResponse({"error": "Returned plan must contain a non-empty 'slots' list."}, status=502)
    for idx, slot in enumerate(slots):
        if not isinstance(slot, dict):
            return JsonResponse({"error": f"Slot {idx} is not an object."}, status=502)
        if "time" not in slot or "label" not in slot or "description" not in slot:
            return JsonResponse({"error": f"Slot {idx} is missing required fields."}, status=502)
        slot.setdefault("protein_g", 0)
        slot.setdefault("carbs_g", 0)
        slot.setdefault("calories_kcal", 0)
    # Return plan to frontend; do not store until user clicks "Insert this to my plan"
    return JsonResponse({"ok": True, "plan": plan})


def _totals_from_plan_slots(slots, checked):
    """Compute protein, carbs, energy totals from plan slots using checked list."""
    total_protein = total_carbs = total_energy = 0
    if not slots or not isinstance(checked, list):
        return 0, 0, 0
    for idx, slot in enumerate(slots):
        if idx < len(checked) and checked[idx] and isinstance(slot, dict):
            total_protein += float(slot.get("protein_g", 0) or 0)
            total_carbs += float(slot.get("carbs_g", 0) or 0)
            total_energy += float(slot.get("calories_kcal", 0) or 0)
    return total_protein, total_carbs, total_energy


@login_required
@require_http_methods(["POST"])
def find_order_options(request):
    """
    Find online ordering options for a dish within a price range.
    Expects JSON: { "dish_name": str, "description": str (optional), "price_range": str }
    Returns: { "options": str } or { "error": str }
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
        dish_name = (body.get("dish_name") or "").strip()
        description = (body.get("description") or "").strip()
        price_range = (body.get("price_range") or "mid-range").strip()
        if not dish_name:
            return JsonResponse({"error": "Dish name required"}, status=400)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # Map price range to description
    price_descriptions = {
        "budget": "₹50 - ₹200 (affordable, budget-friendly options)",
        "mid-range": "₹200 - ₹500 (good quality, mid-range options)",
        "premium": "₹500+ (high-quality, premium options)",
    }
    price_desc = price_descriptions.get(price_range, price_descriptions["mid-range"])
    
    # Build prompt for ordering information
    prompt = f"Where can I order '{dish_name}'"
    if description:
        prompt += f" ({description})"
    prompt += f" online? Price range: {price_desc}. "
    prompt += "Provide 3-5 specific online platforms or restaurants (like Swiggy, Zomato, etc.) where this dish can be ordered. "
    prompt += "Include platform names, approximate prices, and any helpful tips. Keep it concise and practical."
    
    system_instruction = (
        "You are a helpful food ordering assistant. Provide practical information about "
        "where users can order specific dishes online. Focus on popular food delivery platforms "
        "and restaurants. Be specific about price ranges and availability."
    )
    
    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    options_text, err = _call_gemini(prompt, system_instruction, api_key, history=None)
    
    if err:
        return JsonResponse({"error": err}, status=503)
    return JsonResponse({"options": options_text})


@login_required
@require_http_methods(["POST"])
def generate_recipe(request):
    """
    Generate a recipe for a specific dish.
    Expects JSON: { "dish_name": str, "description": str (optional) }
    Returns: { "recipe": str } or { "error": str }
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
        dish_name = (body.get("dish_name") or "").strip()
        description = (body.get("description") or "").strip()
        if not dish_name:
            return JsonResponse({"error": "Dish name required"}, status=400)
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # Build prompt for recipe generation
    prompt = f"Provide a simple, clear recipe for: {dish_name}"
    if description:
        prompt += f" ({description})"
    prompt += ". Include ingredients list and step-by-step instructions. Keep it concise, PCOD-friendly, and easy to follow. Format with clear sections for Ingredients and Instructions."
    
    system_instruction = (
        "You are a helpful recipe assistant. Provide clear, practical recipes "
        "that are suitable for PCOD/PCOS management. Focus on whole foods, balanced nutrition, "
        "and simple cooking methods. Keep recipes concise and easy to follow."
    )
    
    api_key = getattr(settings, "GEMINI_API_KEY", "") or ""
    recipe_text, err = _call_gemini(prompt, system_instruction, api_key, history=None)
    
    if err:
        return JsonResponse({"error": err}, status=503)
    return JsonResponse({"recipe": recipe_text})


@login_required
def diet_plan(request):
    """
    Diet plan page: shows the AI-generated plan from the database,
    with tickable slots and Protein/Carbs/Energy charts. Data is loaded from DietDayLog (plan/note/checked).
    """
    user = request.user
    today = timezone.localdate()
    # Prefer today's log with a plan, else most recent log that has a plan
    obj = DietDayLog.objects.filter(user=user, date=today).exclude(plan__isnull=True).first()
    if obj is None:
        obj = DietDayLog.objects.filter(user=user).exclude(plan__isnull=True).order_by("-date").first()
    if obj is None:
        context = {
            "username": user.username,
            "has_plan": False,
            "today": today,
        }
        return render(request, "tracker/diet_plan.html", context)

    plan = obj.plan
    plan_note = obj.note or ""
    slots = plan.get("slots", []) if isinstance(plan, dict) else []
    if not slots:
        context = {
            "username": user.username,
            "has_plan": False,
            "today": today,
        }
        return render(request, "tracker/diet_plan.html", context)

    checked = obj.checked if isinstance(obj.checked, list) else []
    if len(checked) != len(slots):
        checked = [False] * len(slots)

    if request.method == "POST":
        new_checked = []
        for idx in range(len(slots)):
            key = f"slot_{idx}"
            new_checked.append(bool(request.POST.get(key)))
        obj.checked = new_checked
        obj.save(update_fields=["checked"])
        return redirect("tracker:diet_plan")

    # Totals for the displayed plan (for pie chart / today bar)
    total_protein, total_carbs, total_energy = _totals_from_plan_slots(slots, checked)

    # 7-day bar chart from database: for each of last 7 days, get DietDayLog with plan and compute totals
    labels = []
    protein_series = []
    carbs_series = []
    energy_series = []
    plan_by_date = {}
    for p in DietDayLog.objects.filter(user=user, date__gte=today - timedelta(days=6), date__lte=today).exclude(plan__isnull=True):
        slots_p = p.plan.get("slots", []) if isinstance(p.plan, dict) else []
        checked_p = p.checked if isinstance(p.checked, list) else []
        plan_by_date[p.date] = _totals_from_plan_slots(slots_p, checked_p)
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        labels.append(day.strftime("%d %b"))
        totals = plan_by_date.get(day, (0, 0, 0))
        protein_series.append(totals[0])
        carbs_series.append(totals[1])
        energy_series.append(totals[2])
    # Ensure today's bar uses current page totals (in case we just loaded and haven't re-queried)
    if obj.date == today:
        protein_series[6] = total_protein
        carbs_series[6] = total_carbs
        energy_series[6] = total_energy

    chart_labels_json = json.dumps(labels)
    chart_protein_json = json.dumps(protein_series)
    chart_carbs_json = json.dumps(carbs_series)
    chart_energy_json = json.dumps(energy_series)

    slots_with_state = list(zip(slots, checked))
    context = {
        "username": user.username,
        "has_plan": True,
        "today": today,
        "plan": plan,
        "plan_note": plan_note,
        "slots_with_state": slots_with_state,
        "chart_labels_json": chart_labels_json,
        "chart_protein_json": chart_protein_json,
        "chart_carbs_json": chart_carbs_json,
        "chart_energy_json": chart_energy_json,
    }
    return render(request, "tracker/diet_plan.html", context)
