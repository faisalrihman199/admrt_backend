cp db.sqlite3 db_backup.sqlite3
python3 manage.py makemigrations
python3 manage.py migrate