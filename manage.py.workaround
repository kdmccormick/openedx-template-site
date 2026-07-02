#!/bin/bash
# A passthru until we get wip_manage.py working.

for envvar in \
        "DJANGO_SETTINGS_MODULE" \
        "STATIC_ROOT_LMS" \
        "STATIC_ROOT_CMS" \
        "LMS_CFG" \
        "CMS_CFG" ; do
    >&2 echo "$envvar=${!envvar}"
done

case "$DJANGO_SETTINGS_MODULE" in
    *lms*) system="lms" ;;
    *cms*) system="cms" ;;
    *)
        >&2 echo "could not determine system for settings $DJANGO_SETTINGS_MODULE"
        exit 1
        ;;
esac

set -x
cd ../openedx-platform && ./manage.py "$system" "$@"
