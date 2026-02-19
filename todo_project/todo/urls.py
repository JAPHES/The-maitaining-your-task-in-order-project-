from django.urls import path
from . import views


urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('calendar/', views.calendar_view, name='task_calendar'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/delete/<int:pk>/', views.task_delete, name='task_delete'),
    path('task/update/<int:pk>/', views.task_update, name='task_update'),
    path('trash/', views.task_trash, name='task_trash'),
    path('statistics/', views.stats_view, name='task_statistics'),
    path('todo/', views.todo_view, name='todo'),
]





