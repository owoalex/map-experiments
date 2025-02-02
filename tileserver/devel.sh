#!/bin/bash
if [ -f .env ]; then
    echo "Using local .env"
else
    echo "Copying .env from project root (../.env)"
    cp ../.env .env
fi
source .env
cd ../
docker compose up -d postgis
export POSTGRES_DB=$POSTGRES_DB
export POSTGRES_USER=$POSTGRES_USER
export POSTGRES_PASSWORD=$POSTGRES_PASSWORD
export POSTGRES_HOST="localhost"
cd tileserver/src
pwd
gunicorn -w 1 main:app -b 0.0.0.0
