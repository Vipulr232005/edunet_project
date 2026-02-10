import json
import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from django.core.mail import send_mail
from .forms import SignUpForm, DailyLogForm, NotificationPreferenceForm
from .models import DailyLog, DietDayLog, NotificationPreference

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
    # Build simple list for last 7 days wellness
    wellness_days = [
        {'date': log.date, 'wellness': log.wellness_score, 'mood': log.mood, 'sleep': log.sleep_quality}
        for log in last_7
    ]
    context = {
        'username': user.username,
        'wellness_score': wellness_score,
        'sleep_quality': sleep_quality,
        'mood': mood,
        'wellness_days': wellness_days,
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


@login_required
def diet_plan(request):
    """Diet plan page: show today's plan (Day N by weekday), tick slots, graph of protein/carbs/energy."""
    user = request.user
    today = timezone.localdate()
    weekday_index = today.weekday()  # 0=Monday, 6=Sunday
    day_number = weekday_index + 1  # Day 1 = Monday, ..., Day 7 = Sunday
    day_plan = DIET_PLAN[weekday_index]
    day_name = WEEKDAY_NAMES[weekday_index]

    log, _ = DietDayLog.objects.get_or_create(user=user, date=today, defaults={})

    # Add checked flag for each slot for the template
    for item in day_plan:
        item['checked'] = getattr(log, item['slot'], False)

    if request.method == 'POST':
        for slot_key in DIET_SLOT_MACROS.keys():
            setattr(log, slot_key, slot_key in request.POST)
        log.save()
        return redirect('tracker:diet_plan')

    # Last 14 days for chart: protein, carbs, energy from ticked slots
    last_14_logs = (
        DietDayLog.objects.filter(user=user, date__lte=today)
        .order_by('-date')[:14]
    )
    last_14_list = list(last_14_logs)
    last_14_list.reverse()
    chart_labels = [d.date.strftime('%d %b') for d in last_14_list]
    chart_protein = []
    chart_carbs = []
    chart_energy = []
    for d in last_14_list:
        p, c, e = 0, 0, 0
        for slot_key, (mp, mc, me) in DIET_SLOT_MACROS.items():
            if getattr(d, slot_key):
                p += mp
                c += mc
                e += me
        chart_protein.append(p)
        chart_carbs.append(c)
        chart_energy.append(e)

    context = {
        'username': user.username,
        'day_number': day_number,
        'day_name': day_name,
        'day_plan': day_plan,
        'log': log,
        'today': today,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_protein_json': json.dumps(chart_protein),
        'chart_carbs_json': json.dumps(chart_carbs),
        'chart_energy_json': json.dumps(chart_energy),
    }
    return render(request, 'tracker/diet_plan.html', context)


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


@login_required
def notification_settings(request):
    """Settings page: toggle notification types, show email that will receive notifications."""
    user = request.user
    prefs, _ = NotificationPreference.objects.get_or_create(user=user, defaults={})
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            return redirect('tracker:notification_settings')
    else:
        form = NotificationPreferenceForm(instance=prefs)
    return render(request, 'tracker/notification_settings.html', {
        'form': form,
        'notification_email': getattr(user, 'email', '') or '',
    })
