from django.shortcuts  import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

# Create your views here.
## a methods to list our tasks
## a method to list our tasks
## a method to create the task
from .models import Task
from .forms import TaskForm


def _ordered_tasks(queryset):
    return queryset.order_by(
        '-is_pinned',
        F('due_date').asc(nulls_last=True),
        'id',
    )


def _task_stats(queryset):
    total = queryset.count()
    completed = queryset.filter(completed=True).count()
    pending = total - completed
    percentage = int((completed / total) * 100) if total else 0
    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'percentage': percentage,
    }


# method to list task
@login_required
def task_list(request):
    tasks_queryset = Task.objects.filter(owner=request.user, is_deleted=False)
    status = request.GET.get('status', 'all').lower()

    if status == 'completed':
        tasks_queryset = tasks_queryset.filter(completed=True)
    elif status == 'pending':
        tasks_queryset = tasks_queryset.filter(completed=False)
    else:
        status = 'all'

    if request.method == "POST":
        action = request.POST.get('action')
        base_queryset = Task.objects.filter(owner=request.user, is_deleted=False)
        if action == 'mark_all_completed':
            base_queryset.filter(completed=False).update(
                completed=True,
                completed_at=timezone.now(),
            )
        elif action == 'mark_all_pending':
            base_queryset.filter(completed=True).update(
                completed=False,
                completed_at=None,
            )
        elif action == 'trash_completed':
            base_queryset.filter(completed=True).update(is_deleted=True)
        return redirect(f"{request.path}?status={status}")

    tasks = _ordered_tasks(tasks_queryset)
    stats = _task_stats(Task.objects.filter(owner=request.user, is_deleted=False))

    return render(request, 'todo/task_list.html', {
        'tasks': tasks,
        'status': status,
        'today': timezone.localdate(),
        **stats,
    })

@login_required
def task_create(request):
    #cover validity
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.save()
            return redirect('task_list')

    else:
        form = TaskForm()
    return render(request, 'todo/task_form.html', {'form': form})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user, is_deleted=False)
    if request.method == "POST":
        task.is_deleted = True
        task.save(update_fields=['is_deleted'])
        return redirect('task_list')
    return render(request, 'todo/task_confirm_delete.html',{'task': task})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user, is_deleted=False)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
            form = TaskForm(instance=task)
    return render(request, 'todo/task_form.html', {'form':form})

@login_required
def todo_view(request):
    return redirect('task_list')


@login_required
def task_trash(request):
    trash_queryset = Task.objects.filter(owner=request.user, is_deleted=True)

    if request.method == "POST":
        action = request.POST.get('action')
        task_id = request.POST.get('task_id')

        if action == 'restore_all':
            trash_queryset.update(is_deleted=False)
        elif action == 'empty_trash':
            trash_queryset.delete()
        elif action == 'restore_task' and task_id:
            Task.objects.filter(
                pk=task_id,
                owner=request.user,
                is_deleted=True,
            ).update(is_deleted=False)
        elif action == 'delete_forever' and task_id:
            Task.objects.filter(
                pk=task_id,
                owner=request.user,
                is_deleted=True,
            ).delete()

        return redirect('task_trash')

    tasks = _ordered_tasks(trash_queryset)
    return render(request, 'todo/task_trash.html', {'tasks': tasks})


@login_required
def stats_view(request):
    now = timezone.now()
    today = timezone.localdate()

    base_queryset = Task.objects.filter(owner=request.user, is_deleted=False)
    completed_queryset = base_queryset.filter(completed=True, completed_at__isnull=False)

    week_start = now - timedelta(days=7)
    weekly_completed = completed_queryset.filter(completed_at__gte=week_start).count()

    monthly_completed = completed_queryset.filter(
        completed_at__year=now.year,
        completed_at__month=now.month,
    ).count()

    most_used_category_data = (
        base_queryset
        .values('category')
        .annotate(count=Count('category'))
        .order_by('-count')
        .first()
    )
    most_used_category = (
        dict(Task.CATEGORY_CHOICES).get(most_used_category_data['category'], 'N/A')
        if most_used_category_data else 'N/A'
    )

    weekly_labels = []
    weekly_values = []
    for days_back in range(6, -1, -1):
        day = today - timedelta(days=days_back)
        label = day.strftime('%a')
        count = completed_queryset.filter(completed_at__date=day).count()
        weekly_labels.append(label)
        weekly_values.append(count)

    monthly_labels = []
    monthly_values = []
    for month_offset in range(5, -1, -1):
        month = now.month - month_offset
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        month_label = now.replace(year=year, month=month, day=1).strftime('%b %Y')
        count = completed_queryset.filter(
            completed_at__year=year,
            completed_at__month=month,
        ).count()
        monthly_labels.append(month_label)
        monthly_values.append(count)

    return render(request, 'todo/task_statistics.html', {
        'weekly_completed': weekly_completed,
        'monthly_completed': monthly_completed,
        'most_used_category': most_used_category,
        'weekly_labels': weekly_labels,
        'weekly_values': weekly_values,
        'monthly_labels': monthly_labels,
        'monthly_values': monthly_values,
    })


@login_required
def calendar_view(request):
    tasks = Task.objects.filter(
        owner=request.user,
        is_deleted=False,
    ).filter(
        Q(start_date__isnull=False) | Q(due_date__isnull=False)
    ).order_by('start_date', 'due_date')

    events = []
    for task in tasks:
        event_start = task.start_date or task.due_date
        if not event_start:
            continue
        events.append({
            'title': task.title,
            'start': event_start.isoformat(),
            'url': f"/todo/task/update/{task.pk}/",
            'color': '#16a34a' if task.completed else '#0ea5e9',
            'textColor': '#ffffff',
            'extendedProps': {
                'category': task.get_category_display(),
                'priority': task.get_priority_display(),
                'completed': task.completed,
                'dueDate': task.due_date.isoformat() if task.due_date else None,
            }
        })

    return render(request, 'todo/task_calendar.html', {
        'calendar_events': events,
    })
