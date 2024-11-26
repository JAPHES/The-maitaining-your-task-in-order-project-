from django.urls import path
# from .views import register_view, login_view, home_view
from . import views
from todo.views import task_list

urlpatterns = [
    path('', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('todo/', task_list, name='todoapp')
]