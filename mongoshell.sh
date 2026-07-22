#!/bin/bash
set -euo pipefail

docker compose exec mongo \
    mongosh \
    --username="$MONGO_USER" \
    --password="$MONGO_PASSWORD" \
    --authenticationDatabase=admin \
    --host="$MONGO_HOST" \
    --port="$MONGO_PORT" \
    "$MONGO_DATABASE" \
    "$@"
