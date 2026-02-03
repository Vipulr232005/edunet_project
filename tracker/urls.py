from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cycle-tracker/', views.cycle_tracker, name='cycle_tracker'),
    path('wellness/', views.wellness, name='wellness'),
    path('insights/', views.insights, name='insights'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
