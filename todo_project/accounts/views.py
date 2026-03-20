from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from todo.models import Todo
from todo.utils import (
    calculate_user_completion_rate,
    database_health,
    export_to_csv,
    format_duration,
    generate_random_password,
    get_chart_data,
)
from .forms import CustomUserCreationForm, CustomUserProfileForm

User = get_user_model()

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60


def health(request):
    return HttpResponse("OK")


def _get_client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _login_attempt_keys(username, ip_address):
    safe_username = (username or '').strip().lower()
    return (
        f'login_attempts:{ip_address}:{safe_username}',
        f'login_lock_until:{ip_address}:{safe_username}',
    )


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account was created successfully!')
            return redirect("login")
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'accounts/login.html')

        ip_address = _get_client_ip(request)
        attempts_key, lock_key = _login_attempt_keys(username, ip_address)

        lock_until = cache.get(lock_key)
        if lock_until and lock_until > timezone.now().timestamp():
            remaining = int(lock_until - timezone.now().timestamp())
            wait_minutes = max(1, remaining // 60)
            messages.error(request, f"Too many failed attempts. Try again in about {wait_minutes} minute(s).")
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            cache.delete(attempts_key)
            cache.delete(lock_key)
            return redirect("task_list")
        else:
            attempts = cache.get(attempts_key, 0) + 1
            cache.set(attempts_key, attempts, LOGIN_LOCKOUT_SECONDS)
            if attempts >= MAX_LOGIN_ATTEMPTS:
                lock_until_timestamp = timezone.now().timestamp() + LOGIN_LOCKOUT_SECONDS
                cache.set(lock_key, lock_until_timestamp, LOGIN_LOCKOUT_SECONDS)
                messages.error(request, "Too many failed login attempts. Account access temporarily locked.")
            else:
                remaining_tries = MAX_LOGIN_ATTEMPTS - attempts
                messages.error(request, f"Invalid username or password. {remaining_tries} attempt(s) left before temporary lock.")
            return render(request, 'accounts/login.html')
    return render(request, 'accounts/login.html')


@login_required
def home_view(request):
    return redirect("task_list")


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("login")


@login_required
def profile_view(request):
    user = request.user
    if request.method == "POST":
        form = CustomUserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = CustomUserProfileForm(instance=user)
    return render(request, "accounts/profile.html", {"form": form})


# ----------------------------- Admin dashboard views -----------------------------

def _paginate(request, queryset, per_page):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@staff_member_required
def admin_dashboard(request):
    today = timezone.localdate()
    users_qs = User.objects.all()
    tasks_qs = Todo.objects.select_related('user')

    total_users = users_qs.count()
    active_users = users_qs.filter(is_active=True).count()
    new_users_today = users_qs.filter(date_joined__date=today).count()

    total_tasks = tasks_qs.count()
    active_tasks = tasks_qs.filter(is_deleted=False).count()
    completed_tasks = tasks_qs.filter(is_completed=True, is_deleted=False).count()
    pending_tasks = active_tasks - completed_tasks
    trash_tasks = tasks_qs.filter(is_deleted=True).count()
    overdue_tasks = tasks_qs.filter(
        is_deleted=False,
        is_completed=False,
        due_date__lt=today,
    ).count()
    completion_rate_percentage = int((completed_tasks / active_tasks) * 100) if active_tasks else 0

    top_10_users = (
        users_qs.annotate(
            task_count=Count('todos'),
            completed_count=Count('todos', filter=Q(todos__is_completed=True)),
        )
        .annotate(completion_rate=Count('todos', filter=Q(todos__is_completed=True)) * 100.0 / (Count('todos') + 0.0001))
        .order_by('-task_count')[:10]
    )

    recent_10_users = (
        users_qs.annotate(
            task_count=Count('todos'),
        )
        .order_by('-date_joined')[:10]
    )

    recent_10_tasks = tasks_qs.order_by('-created_at')[:10]

    chart_data = get_chart_data()

    recent_activity = []
    for task in tasks_qs.order_by('-updated_at')[:5]:
        recent_activity.append({
            'type': 'task_completed' if task.is_completed else 'task_updated',
            'title': task.title,
            'user': getattr(task.user, 'email', 'N/A'),
            'timestamp': task.updated_at,
        })
    for user in recent_10_users[:2]:
        recent_activity.append({
            'type': 'user_joined',
            'user': user.email,
            'timestamp': user.date_joined,
        })
    recent_activity = sorted(recent_activity, key=lambda x: x['timestamp'], reverse=True)[:5]

    db_health = database_health()

    avg_tasks_per_user = round(total_tasks / total_users, 2) if total_users else 0

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'new_users_today': new_users_today,
        'total_tasks': total_tasks,
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'trash_tasks': trash_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate_percentage': completion_rate_percentage,
        'last_7_days': chart_data['last_7_days'],
        'category_distribution': chart_data['category_distribution'],
        'priority_distribution': chart_data['priority_distribution'],
        'top_10_users': top_10_users,
        'recent_10_users': recent_10_users,
        'recent_10_tasks': recent_10_tasks,
        'recent_activity': recent_activity,
        'attachments_count': chart_data['attachments_count'],
        'disk_usage_bytes': chart_data['disk_usage_bytes'],
        'avg_tasks_per_user': avg_tasks_per_user,
        **db_health,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@staff_member_required
def admin_users(request):
    search = (request.GET.get('search') or '').strip()
    status = (request.GET.get('status') or 'all').lower()

    users = User.objects.annotate(
        task_count=Count('todos'),
        completed_count=Count('todos', filter=Q(todos__is_completed=True)),
    )
    if search:
        users = users.filter(Q(email__icontains=search) | Q(username__icontains=search))
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)

    if request.method == "POST":
        action = request.POST.get('action')
        ids = request.POST.getlist('selected')
        selected_qs = users.filter(id__in=ids) if ids else User.objects.none()
        if action == 'activate':
            selected_qs.update(is_active=True)
            messages.success(request, f"Activated {selected_qs.count()} user(s).")
        elif action == 'deactivate':
            selected_qs.update(is_active=False)
            messages.success(request, f"Deactivated {selected_qs.count()} user(s).")
        elif action == 'export':
            return export_to_csv(selected_qs, ['id', 'email', 'username', 'date_joined', 'last_login'], 'users.csv')
        return redirect(request.path)

    page_obj = _paginate(request, users.order_by('-date_joined'), 20)

    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'users_with_zero_tasks': User.objects.annotate(task_count=Count('todos')).filter(task_count=0).count(),
    }

    return render(request, 'accounts/admin_users.html', {
        'page_obj': page_obj,
        'search': search,
        'status': status,
        **stats,
    })


@staff_member_required
@require_POST
def admin_user_toggle(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    messages.success(request, f"{'Activated' if user.is_active else 'Deactivated'} {user.email}.")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'is_active': user.is_active})
    return redirect('admin_users')


@staff_member_required
@require_POST
def admin_user_reset_password(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    new_password = generate_random_password()
    user.set_password(new_password)
    user.save(update_fields=['password'])
    messages.success(request, f"New password generated for {user.email}.")
    return JsonResponse({'status': 'ok', 'password': new_password})


@staff_member_required
@require_POST
def admin_user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    confirm = request.POST.get('confirm_password')
    if confirm and not request.user.check_password(confirm):
        return HttpResponseBadRequest("Invalid confirmation password.")
    user.delete()
    messages.success(request, "User deleted.")
    return redirect('admin_users')


@staff_member_required
def admin_user_tasks(request, user_id):
    admin_user = get_object_or_404(User, pk=user_id)

    status = (request.GET.get('status') or 'all').lower()
    category = (request.GET.get('category') or '').lower()
    priority = (request.GET.get('priority') or '').lower()
    search = (request.GET.get('search') or '').strip()

    tasks = Todo.objects.select_related('user').prefetch_related('notes', 'resources').filter(user=admin_user)
    if status == 'completed':
        tasks = tasks.filter(is_completed=True, is_deleted=False)
    elif status == 'active':
        tasks = tasks.filter(is_completed=False, is_deleted=False)
    elif status == 'trash':
        tasks = tasks.filter(is_deleted=True)

    if category:
        tasks = tasks.filter(category=category)
    if priority:
        tasks = tasks.filter(priority=priority)
    if search:
        tasks = tasks.filter(title__icontains=search)

    if request.method == "POST":
        action = request.POST.get('action')
        ids = request.POST.getlist('selected')
        selected_qs = tasks.filter(id__in=ids)
        if action == 'complete':
            selected_qs.update(is_completed=True, completed_at=timezone.now())
        elif action == 'pending':
            selected_qs.update(is_completed=False, completed_at=None)
        elif action == 'trash':
            selected_qs.update(is_deleted=True)
        elif action == 'restore':
            selected_qs.update(is_deleted=False)
        elif action == 'delete':
            selected_qs.delete()
        return redirect(request.path)

    page_obj = _paginate(request, tasks.order_by('-created_at'), 20)

    header_stats = admin_user.todos.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(is_completed=True)),
        pending=Count('id', filter=Q(is_completed=False, is_deleted=False)),
    )
    header_stats['completion_rate'] = calculate_user_completion_rate(admin_user)

    return render(request, 'accounts/admin_user_tasks.html', {
        'admin_user': admin_user,
        'page_obj': page_obj,
        'status': status,
        'category': category,
        'priority': priority,
        'search': search,
        'today': timezone.localdate(),
        **header_stats,
    })


@staff_member_required
def admin_tasks(request):
    status = (request.GET.get('status') or 'all').lower()
    category = request.GET.getlist('category') or []
    priority = request.GET.getlist('priority') or []
    user_search = (request.GET.get('user') or '').strip()
    created_from = request.GET.get('created_from')
    created_to = request.GET.get('created_to')
    due_from = request.GET.get('due_from')
    due_to = request.GET.get('due_to')
    text_search = (request.GET.get('q') or '').strip()

    tasks = Todo.objects.select_related('user').prefetch_related('notes', 'resources').all()
    if status == 'completed':
        tasks = tasks.filter(is_completed=True, is_deleted=False)
    elif status == 'active':
        tasks = tasks.filter(is_completed=False, is_deleted=False)
    elif status == 'trash':
        tasks = tasks.filter(is_deleted=True)

    if category:
        tasks = tasks.filter(category__in=category)
    if priority:
        tasks = tasks.filter(priority__in=priority)
    if user_search:
        tasks = tasks.filter(Q(user__email__icontains=user_search) | Q(user__username__icontains=user_search))
    if created_from:
        tasks = tasks.filter(created_at__date__gte=created_from)
    if created_to:
        tasks = tasks.filter(created_at__date__lte=created_to)
    if due_from:
        tasks = tasks.filter(due_date__gte=due_from)
    if due_to:
        tasks = tasks.filter(due_date__lte=due_to)
    if text_search:
        tasks = tasks.filter(Q(title__icontains=text_search) | Q(description__icontains=text_search))

    if request.method == "POST":
        action = request.POST.get('action')
        ids = request.POST.getlist('selected')
        selected_qs = tasks.filter(id__in=ids)
        if action == 'complete':
            selected_qs.update(is_completed=True, completed_at=timezone.now())
        elif action == 'pending':
            selected_qs.update(is_completed=False, completed_at=None)
        elif action == 'trash':
            selected_qs.update(is_deleted=True)
        elif action == 'restore':
            selected_qs.update(is_deleted=False)
        elif action == 'delete':
            selected_qs.delete()
        elif action == 'export':
            return export_to_csv(
                selected_qs,
                ['id', 'title', 'description', 'category', 'priority', 'due_date', 'is_completed', 'is_deleted'],
                'tasks.csv'
            )
        return redirect(request.path)

    if request.GET.get('export') == '1':
        return export_to_csv(
            tasks,
            ['id', 'title', 'description', 'category', 'priority', 'due_date', 'is_completed', 'is_deleted'],
            'tasks_filtered.csv'
        )

    page_obj = _paginate(request, tasks.order_by('-created_at'), 50)

    quick_stats = {
        'total_tasks': Todo.objects.count(),
        'active_tasks': Todo.objects.filter(is_deleted=False).count(),
        'completed_tasks': Todo.objects.filter(is_completed=True, is_deleted=False).count(),
        'trash_tasks': Todo.objects.filter(is_deleted=True).count(),
        'overdue_tasks': Todo.objects.filter(is_completed=False, is_deleted=False, due_date__lt=timezone.localdate()).count(),
    }

    return render(request, 'accounts/admin_tasks.html', {
        'page_obj': page_obj,
        'status': status,
        'category': category,
        'priority': priority,
        'user_search': user_search,
        'created_from': created_from,
        'created_to': created_to,
        'due_from': due_from,
        'due_to': due_to,
        'text_search': text_search,
        'today': timezone.localdate(),
        **quick_stats,
    })


@staff_member_required
@require_POST
def admin_task_force_delete(request, task_id):
    task = get_object_or_404(Todo, pk=task_id)
    task.delete()
    messages.success(request, "Task permanently deleted.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_tasks'))


@staff_member_required
@require_POST
def admin_task_restore(request, task_id):
    task = get_object_or_404(Todo, pk=task_id)
    task.is_deleted = False
    task.save(update_fields=['is_deleted'])
    messages.success(request, "Task restored.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_tasks'))


@staff_member_required
@require_POST
def admin_task_toggle_complete(request, task_id):
    task = get_object_or_404(Todo, pk=task_id)
    task.is_completed = not task.is_completed
    if task.is_completed:
        task.completed_at = timezone.now()
    else:
        task.completed_at = None
    task.save(update_fields=['is_completed', 'completed_at'])
    messages.success(request, "Task status updated.")
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'is_completed': task.is_completed})
    return redirect(request.META.get('HTTP_REFERER', 'admin_tasks'))


@staff_member_required
def admin_export_users(request):
    qs = User.objects.annotate(
        task_count=Count('todos'),
        completed_count=Count('todos', filter=Q(todos__is_completed=True)),
    )
    return export_to_csv(qs, ['id', 'email', 'username', 'task_count', 'completed_count', 'date_joined'], 'all_users.csv')


@staff_member_required
def admin_export_tasks(request):
    qs = Todo.objects.select_related('user')
    return export_to_csv(qs, ['id', 'title', 'category', 'priority', 'due_date', 'is_completed', 'is_deleted'], 'all_tasks.csv')
