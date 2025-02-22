#!/bin/bash
if [ -f .env ]; then
    echo "Using local .env"
else
    echo "Copying .env from project root (../.env)"
    cp ../.env .env
fi
source .env
cd ../
docker compose up -d couchdb
export GRIPPY_CONFIG_FILE="../../config/grippymap-devel.json"
cd osmextractor/src
python3 main.py
