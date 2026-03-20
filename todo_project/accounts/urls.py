from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health),
    path('', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # Admin dashboard routes
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/users/<int:user_id>/tasks/', views.admin_user_tasks, name='admin_user_tasks'),
    path('admin/users/<int:user_id>/toggle/', views.admin_user_toggle, name='admin_user_toggle'),
    path('admin/users/<int:user_id>/reset-password/', views.admin_user_reset_password, name='admin_user_reset_password'),
    path('admin/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('admin/tasks/', views.admin_tasks, name='admin_tasks'),
    path('admin/tasks/<int:task_id>/force-delete/', views.admin_task_force_delete, name='admin_task_force_delete'),
    path('admin/tasks/<int:task_id>/restore/', views.admin_task_restore, name='admin_task_restore'),
    path('admin/tasks/<int:task_id>/toggle-complete/', views.admin_task_toggle_complete, name='admin_task_toggle_complete'),
    path('admin/export/users/', views.admin_export_users, name='admin_export_users'),
    path('admin/export/tasks/', views.admin_export_tasks, name='admin_export_tasks'),
]
