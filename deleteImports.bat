@echo off
REM This batch file enters the Django shell and deletes all FileImport models

REM Activate your virtual environment if needed
REM call path\to\venv\Scripts\activate

REM Change directory to your Django project root (where manage.py is)
cd /d %~dp0

REM Run Django shell and execute the deletion
python manage.py shell -c "from ingestion.models import FileImport; FileImport.objects.all().delete()"