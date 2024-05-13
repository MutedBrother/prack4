FROM postgres:14-alpine

COPY ./init.sql /docker-entrypoint-initdb.d/init.sql

CMD chmod 0666 /tmp/postgresql.log
