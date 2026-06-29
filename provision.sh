#!/bin/bash

./manage.py shell -c '
from django.contrib.auth import get_user_model
from common.djangoapps.student.models import UserProfile
User = get_user_model()
user, _ = User.objects.get_or_create(
    username="openedx",
    defaults={"email": "openedx@local.openedx.io"},
)
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.set_password("openedx")
user.save()
UserProfile.objects.get_or_create(
    user=user,
    defaults={"name": "openedx"},
)
'

# Register the CMS (Studio) SSO OAuth2 client in the LMS, so Studio can
# authenticate users against the LMS via social-auth (edx-oauth2). Owned by a
# dedicated "cms" service user. Both commands are idempotent (manage_user is a
# no-op if the user exists; create_dot_application --update updates in place).
# Key/secret come from env_vars and must match settings_cms_dev.py.
# https://github.com/openedx/edx-platform/blob/master/docs/guides/studio_oauth.rst
./manage.py manage_user cms cms@local.openedx.io --unusable-password
./manage.py create_dot_application \
    --grant-type authorization-code \
    --skip-authorization \
    --redirect-uris "http://studio.local.openedx.io:8001/complete/edx-oauth2/" \
    --client-id "$CMS_SSO_OAUTH2_KEY" \
    --client-secret "$CMS_SSO_OAUTH2_SECRET" \
    --scopes user_id \
    --update \
    cms-sso-dev cms
