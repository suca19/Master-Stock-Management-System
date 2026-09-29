#!/bin/sh
# Runs once, when MySQL initialises an empty data volume.
# Lets the app user create and drop Django's test database (test_<MYSQL_DATABASE>).
mysql --protocol=socket -uroot -p"$MYSQL_ROOT_PASSWORD" <<SQL
GRANT ALL PRIVILEGES ON \`test_${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'%';
FLUSH PRIVILEGES;
SQL
