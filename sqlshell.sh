#!/bin/bash
set -euo pipefail

# Open a root MySQL shell inside the mysql container.
source "$(dirname "$0")/env"

docker compose exec mysql \
    mysql \
    --user="$MYSQL_ROOT_USERNAME" \
    --password="$MYSQL_ROOT_PASSWORD" \
    --host="$MYSQL_HOST" \
    --port="$MYSQL_PORT" \
    --default-character-set=utf8mb4 \
    --database="$MYSQL_DATABASE" \
    "$@"
