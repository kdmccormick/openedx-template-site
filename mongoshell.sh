#!/bin/bash
set -euo pipefail

docker compose exec mongo \
    mongosh \
    --username="$MONGO_INITDB_ROOT_USERNAME" \
    --password="$MONGO_INITDB_ROOT_PASSWORD" \
    --authenticationDatabase=admin \
    --host="$MONGO_HOST" \
    --port="$MONGO_PORT" \
    "$MONGO_INITDB_DATABASE" \
    "$@"
