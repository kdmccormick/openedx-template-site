Warning: This doesn't entirely work yet.

```
uv sync
docker compose up

# assumes that openedx-platform is a sibling dir.
# TODO remove this assumption somehow
export LMS_CFG=../opeendx-platform/lms/envs/minimal.yml
export CMS_CFG="$LMS_CFG"

# Any of the following:
DJANGO_SETTINGS_MODULE=openedx_site.settings_lms ./manage.py runserver
DJANGO_SETTINGS_MODULE=openedx_site.settings_lms_dev ./manage.py runserver
DJANGO_SETTINGS_MODULE=openedx_site.settings_cms ./manage.py runserver
DJANGO_SETTINGS_MODULE=openedx_site.settings_cms_dev ./manage.py runserver
```


