#!/bin/sh
if [ "${DEBUG}" = true ]; then
  cp /etc/nginx/nginx.conf.dev /etc/nginx/nginx.conf
  cp /etc/supervisor.d/supervisor.ini.dev /etc/supervisor.d/supervisor.ini
  pip install -r /code/requirements-dev.txt
  if [ ! -e /code/rially/settings.py ]; then
    cp /code/rially/settings.py.dev /code/rially/settings.py
  fi;
else
  cp /etc/nginx/nginx.conf.prod /etc/nginx/nginx.conf
  cp /etc/supervisor.d/supervisor.ini.prod /etc/supervisor.d/supervisor.ini
  cp /code/rially/settings.py.prod /code/rially/settings.py
fi;

python manage.py waitfordb

python manage.py migrate --run-syncdb

if [ "${DEBUG}" = true ]; then
    python manage.py collectstatic --noinput --link -v 0
else
    python manage.py collectstatic --noinput -v 0
fi;
python manage.py compress

yes yes | python manage.py updatemodel

if [ "${DEBUG}" = true ]; then
  echo "Creating admin account if no accounts exist. . ."
  python manage.py shell --command "from authentication.models import CustomUser; \
                                    u = CustomUser.objects.create_superuser('admin', 'adminadmin') \
                                    if CustomUser.objects.count() <= 0 else \
                                    None"
fi;

exec "$@"