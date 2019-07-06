#!/bin/bash

echo "Waiting for database to start"
./wait-for-it.sh db:5432 --timeout=60 -- echo "Postgres is up"

echo "Starting server"
./manage.py runserver 0.0.0.0:80