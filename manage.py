#!/bin/bash
# A passthru until we get wip_manage.py working.

cd ../openedx-platform && ./manage.py "$@"
