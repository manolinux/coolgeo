#!/bin/sh
#Start Postgres 11
/etc/init.d/postgresql start

#Create database 
su postgres -c /var/lib/postgresql/create_db.sh

# Configure Postgis 2.5
su  postgres -c psql < /var/lib/postgresql/enable_postgis.sql


#Grant permissions
su postgres -c "psql --set USER_RWX=$USER_RWX --set USER_RX=$USER_RX --set PASS_RWX=$PASS_RWX --set PASS_RX=$PASS_RX < /var/lib/postgresql/grant_permissions.sql"

#Import data
su postgres -c /var/lib/postgresql/import_data.sh

/usr/bin/supervisord -n -c /app/supervisor.conf
