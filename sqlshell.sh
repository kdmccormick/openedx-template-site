#!/bin/bash
set -euo pipefail

docker compose exec mysql \
    mysql \
    --user="$MYSQL_ROOT_USERNAME" \
    --password="$MYSQL_ROOT_PASSWORD" \
    --host="$MYSQL_HOST" \
    --port="$MYSQL_PORT" \
    --default-character-set=utf8mb4 \
    --database="$MYSQL_DATABASE" \
    "$@"
