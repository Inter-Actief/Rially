FROM postgres:latest
ADD init-dev-db.sql /docker-entrypoint-initdb.d/init-dev-db.sql
RUN chmod +x /docker-entrypoint-initdb.d/init-dev-db.sql
RUN chmod 777 /var/lib/postgresql/data
