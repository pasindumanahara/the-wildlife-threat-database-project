from django.urls import path

from . import views


urlpatterns = [
    path('csrf/', views.csrf, name='auth-csrf'),
    path('register/', views.register, name='auth-register'),
    path('login/', views.sign_in, name='auth-login'),
    path('logout/', views.sign_out, name='auth-logout'),
    path('me/', views.me, name='auth-me'),
]
