from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cycle-tracker/', views.cycle_tracker, name='cycle_tracker'),
    path('wellness/', views.wellness, name='wellness'),
    path('insights/', views.insights, name='insights'),
    path('diet-plan/', views.diet_plan, name='diet_plan'),
    path('diet-plan/import/', views.diet_plan_import, name='diet_plan_import'),
    path('diet-plan/generate/', views.diet_plan_generate, name='diet_plan_generate'),
    path('diet-plan/generate-recipe/', views.generate_recipe, name='generate_recipe'),
    path('diet-plan/find-order-options/', views.find_order_options, name='find_order_options'),
    path('ai-diet-agent/', views.ai_diet_agent, name='ai_diet_agent'),
    path('ai/support/chat/', views.pcod_support_chat, name='pcod_support_chat'),
    path('ai/diet/chat/', views.diet_planner_chat, name='diet_planner_chat'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='tracker/password_reset_form.html',
        success_url=reverse_lazy('tracker:password_reset_done'),
        email_template_name='tracker/password_reset_email.html',
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='tracker/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='tracker/password_reset_confirm.html', success_url=reverse_lazy('tracker:password_reset_complete')), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='tracker/password_reset_complete.html'), name='password_reset_complete'),
]
