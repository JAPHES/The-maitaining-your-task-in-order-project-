import csv
import secrets
import string
from datetime import timedelta
from pathlib import Path
from typing import Iterable, Sequence

import django
import sys
from django.conf import settings
from django.db import connection
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone

from accounts.models import CustomUser
from .models import TaskNote, Todo


def generate_random_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def export_to_csv(queryset, fields: Sequence[str], filename: str) -> HttpResponse:
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(fields)
    for obj in queryset:
        row = [getattr(obj, field)() if callable(getattr(obj, field)) else getattr(obj, field, '') for field in fields]
        writer.writerow(row)
    return response


def calculate_user_completion_rate(user: CustomUser) -> int:
    totals = user.todos.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(is_completed=True)),
    )
    total = totals.get('total') or 0
    completed = totals.get('completed') or 0
    if not total:
        return 0
    return int((completed / total) * 100)


def format_duration(days: int) -> str:
    if days is None:
        return "Unknown"
    if days < 1:
        return "Today"
    if days == 1:
        return "1 day"
    weeks, remainder = divmod(days, 7)
    parts = []
    if weeks:
        parts.append(f"{weeks} wk{'s' if weeks > 1 else ''}")
    if remainder:
        parts.append(f"{remainder} day{'s' if remainder > 1 else ''}")
    return ' '.join(parts)


def get_chart_data():
    today = timezone.localdate()
    last_7_days = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        created = Todo.objects.filter(created_at__date=day).count()
        completed = Todo.objects.filter(is_completed=True, completed_at__date=day).count()
        last_7_days.append({
            'date': day.strftime('%Y-%m-%d'),
            'created': created,
            'completed': completed,
        })

    category_distribution = list(
        Todo.objects.values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    priority_distribution = list(
        Todo.objects.values('priority')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    attachments_count = TaskNote.objects.exclude(attachment='').count()
    disk_usage_bytes = 0
    media_root = Path(settings.MEDIA_ROOT)
    if media_root.exists():
        for file in media_root.glob('**/*'):
            if file.is_file():
                disk_usage_bytes += file.stat().st_size

    return {
        'last_7_days': last_7_days,
        'category_distribution': category_distribution,
        'priority_distribution': priority_distribution,
        'attachments_count': attachments_count,
        'disk_usage_bytes': disk_usage_bytes,
    }


def database_health():
    try:
        connection.ensure_connection()
        status = 'online'
    except Exception:
        status = 'error'
    return {
        'database_status': status,
        'django_version': django.get_version(),
        'python_version': sys.version.split(' ')[0],
    }
