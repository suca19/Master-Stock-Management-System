#!/bin/sh
set -e

echo "Waiting for MySQL to be available..."
python - <<'PY'
import os, time
try:
    import MySQLdb
except Exception:
    MySQLdb = None
params = {
    'db': os.environ.get('MYSQL_DATABASE'),
    'user': os.environ.get('MYSQL_USER'),
    'passwd': os.environ.get('MYSQL_PASSWORD'),
    'host': os.environ.get('MYSQL_HOST', 'db'),
    'port': int(os.environ.get('MYSQL_PORT', '3306')),
}
# If MYSQL_DATABASE is not set, skip waiting (likely using sqlite)
if not params['db']:
    print('No MYSQL_DATABASE set, skipping MySQL wait')
else:
    while True:
        try:
            if MySQLdb:
                conn = MySQLdb.connect(host=params['host'], user=params['user'], passwd=params['passwd'], db=params['db'], port=params['port'])
                conn.close()
            else:
                # fall back to socket check via tcp
                import socket
                s = socket.socket()
                s.settimeout(1.0)
                s.connect((params['host'], params['port']))
                s.close()
            print('MySQL is available')
            break
        except Exception as e:
            print('MySQL not ready, retrying...', e)
            time.sleep(1)
PY

# Run migrations and collectstatic
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

# Ensure the default admin account exists
python manage.py create_admin

# Execute the container CMD
exec "$@"
