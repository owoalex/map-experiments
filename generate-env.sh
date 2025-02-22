#!/bin/bash
mkdir -p config

POSTGRES_PASSWORD=$(mktemp -u XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)
COUCHDB_ROOT_PASSWORD=$(mktemp -u XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX)

cat > .env << EOF
POSTGRES_DB=gis
POSTGRES_USER=grippy
POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
POSTGRES_HOST="grippymap-postgis"

GUNICORN_WORKERS=8


EOF

mkdir -p config/couchdb
cat > config/couchdb/docker.ini << EOF
[admins]
root = $COUCHDB_ROOT_PASSWORD
single_node = true
EOF

cat > config/grippymap.json << EOF
{
    "couchdb_password": "$COUCHDB_ROOT_PASSWORD",
    "couchdb_user": "root",
    "couchdb_host": "grippymap-couchdb"
}
EOF
