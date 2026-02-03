import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import SignUpForm, DailyLogForm
from .models import DailyLog


def signup(request):
    if request.user.is_authenticated:
        return redirect('tracker:dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tracker:login')
    else:
        form = SignUpForm()
    return render(request, 'tracker/signup.html', {'form': form})


@login_required
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
        form = DailyLogForm(request.POST, instance=today_log)
        if form.is_valid():
            log = form.save(commit=False)
            log.user = user
            log.date = today
            log.save()
            return redirect('tracker:dashboard')
        context['log_form'] = form

    return render(request, 'tracker/dashboard.html', context)
