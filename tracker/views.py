import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone
from .forms import SignUpForm, DailyLogForm
from .models import DailyLog


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

    if today_log:
        symptoms_count = sum(1 for x in [
            today_log.acne_level, today_log.fatigue_level,
            today_log.bloating_level, today_log.sleep_quality
        ] if x is not None)
        if symptoms_count == 0:
            symptoms_count = 1
        context = {
            'username': user.username,
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
