from django.shortcuts  import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required

# Create your views here.
## a methods to list our tasks
## a method to list our tasks
## a method to create the task
from .models import Task
from .forms import TaskForm

# method to list task
@login_required
def task_list(request):
    # all records in the database
    # rows : represent the object / columns
    tasks = Task.objects.all()
    return render(request, 'todo/task_list.html', {'tasks': tasks})

@login_required
def task_create(request):
    #cover validity
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('task_list')

    else:
        form = TaskForm()
    return render(request, 'todo/task_form.html', {'form': form})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        task.delete()
        return redirect('task_list')
    return render(request, 'todo/task_confirm_delete.html',{'task': task})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
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
