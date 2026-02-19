from django.urls import path
from . import views


urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('calendar/', views.calendar_view, name='task_calendar'),
    path('task/create/', views.task_create, name='task_create'),
    path('task/delete/<int:pk>/', views.task_delete, name='task_delete'),
    path('task/update/<int:pk>/', views.task_update, name='task_update'),
    path('task/<int:pk>/notes/add/', views.task_note_add, name='task_note_add'),
    path('task/<int:pk>/notes/<int:note_id>/delete/', views.task_note_delete, name='task_note_delete'),
    path('task/<int:pk>/resources/add/', views.task_resource_add, name='task_resource_add'),
    path('task/<int:pk>/resources/<int:resource_id>/delete/', views.task_resource_delete, name='task_resource_delete'),
    path('trash/', views.task_trash, name='task_trash'),
    path('statistics/', views.stats_view, name='task_statistics'),
    path('todo/', views.todo_view, name='todo'),
]





