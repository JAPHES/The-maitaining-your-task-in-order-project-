# To-Do App

A Django task management app with authentication, scheduling fields, progress tracking, soft delete (trash), and a responsive UI.

## Features
- User authentication (register/login).
- Optional profile image upload and profile editing page.
- Create, update, and manage personal tasks.
- Task metadata:
  - Category (`Personal`, `Work`, `Study`, `Health`, `Other`)
  - Priority (`Low`, `Medium`, `High`)
  - Start/End date and time
  - Due date
  - Pinned tasks
- Task study/workspace extensions:
  - Add multiple notes per task
  - Attach files to notes (lecture handouts, PDFs, screenshots)
  - Add multiple resource links per task (e.g., lecture materials)
- Smart task listing:
  - Soft-deleted tasks excluded by default
  - Ordered by pinned first, then due date
- Status filters:
  - `All`
  - `Done`
  - `Pending`
- Overdue indicator for pending tasks past due date.
- Progress dashboard:
  - Total tasks
  - Completed tasks
  - Pending tasks
  - Completion percentage + progress bar
- Statistics dashboard (`/statistics/`):
  - Completed tasks in last 7 days
  - Completed tasks in current month
  - Most used category
  - Weekly and monthly completion charts (Chart.js)
- Calendar view (`/calendar/`) with FullCalendar:
  - Displays due-date tasks on monthly/weekly/list views
  - Color-codes completed vs pending tasks
  - Click event opens task edit page
- Bulk actions:
  - Mark all completed
  - Mark all pending
  - Move completed tasks to trash
- Trash system (soft delete):
  - Restore one/all tasks
  - Delete forever
- Dark mode toggle (stored in `localStorage`).
- Responsive Bootstrap layout for mobile and desktop.

## Tech Stack
- Backend: Django (Python)
- Frontend: Django templates + Bootstrap 5
- Database: SQLite (local default), PostgreSQL (production)

## Project Structure
- Root: `ToDo/`
- Django project folder: `ToDo/todo_project/`
- Main app: `ToDo/todo_project/todo/`
- Auth app: `ToDo/todo_project/accounts/`

## Setup
1. Clone repository.
2. Open terminal in `ToDo/`.
3. Create and activate virtual environment.
4. Install dependencies.
5. Run migrations.
6. Start server.

```bash
python -m venv env
# Windows
env\Scripts\activate
# Linux/macOS
# source env/bin/activate

pip install -r requirements.txt
cd todo_project
python manage.py migrate
python manage.py runserver
```

## Security Hardening
- Login throttling is enabled (temporary lock after repeated failed attempts).
- Logout is POST-only with CSRF protection.
- Upload validation is enforced:
  - Profile image: allowed image extensions, max 5MB
  - Note attachments: allowed document/image extensions, max 10MB
- Secure defaults are configured in settings (`check --deploy` clean).

Recommended environment variables for production:
```bash
DJANGO_SECRET_KEY=replace_with_long_random_secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECURE_HSTS_SECONDS=31536000
DATABASE_URL=postgres://...
```

## Render Deployment (Free PostgreSQL)
This repository is configured for Render deployment with:
- `render.yaml` (Blueprint for web service + free PostgreSQL database)
- `build.sh` (installs dependencies, runs `collectstatic`, runs migrations)
- `gunicorn` app server
- WhiteNoise static file serving
- `DATABASE_URL` based PostgreSQL config

### Deploy Steps
1. Push this project to GitHub.
2. In Render, click **New +** -> **Blueprint**.
3. Select your repository (Render reads `render.yaml` automatically).
4. Confirm creation of:
   - Web service: `todo-app`
   - PostgreSQL database: `todo-postgres` (free plan)
5. Click **Apply** and wait for first deploy to complete.

After deploy:
- Run `python manage.py createsuperuser` from the Render Shell if you need admin access.
- Media uploads are configured to use a Render persistent disk at `/var/data/media` and are served by Django in production (`DJANGO_SERVE_MEDIA_FILES=True`).
- A persistent disk requires a paid Render web service plan (the blueprint uses `starter` for the web service). PostgreSQL remains on the free plan in this setup.

## Usage
1. Go to `http://127.0.0.1:8000/`.
2. Register and login.
3. Create tasks with category/priority/dates.
4. Use filters and bulk actions on the dashboard.
5. Move tasks to trash and restore when needed.

## Notes
- `Delete` is soft delete (moves to trash).
- Use the `Trash` page for restore or permanent delete.
- Dark mode preference is saved in browser storage.

## License
MIT
