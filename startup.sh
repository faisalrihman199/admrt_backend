 #!/bin/bash
# python manage.py migrate && python manage.py collectstatic && gunicorn --workers 2 admrt.wsgi



python manage.py migrate && python manage.py runserver 0.0.0.0:8000 && python manage.py runserver 0.0.0.0:8000 collectstatic --noinput && waitress-serve --listen=0.0.0.0:8000 admrt.wsgi:application
