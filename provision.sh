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

# Create the Meilisearch backend API key (idempotent), scoped to our index
# prefix. Its value is derived by Meilisearch from MEILI_MASTER_KEY + this uid,
# which is the same value settings_shared derives for MEILISEARCH_API_KEY. This
# is a plain Meilisearch call (no Django), so it runs regardless of system.
python -c "
import os, meilisearch
client = meilisearch.Client('http://localhost:7700', os.environ['MEILI_MASTER_KEY'])
uid = os.environ['MEILISEARCH_API_KEY_UID']
prefix = os.environ['MEILISEARCH_INDEX_PREFIX']
try:
    client.get_key(uid)
    print('Meilisearch API key already exists')
except meilisearch.errors.MeilisearchApiError:
    client.create_key({'name': 'Open edX backend', 'uid': uid, 'actions': ['*'],
                       'indexes': [prefix + '*'], 'expiresAt': None})
    print('Created Meilisearch API key')
"

# Create and populate the Studio search index in Meilisearch. The index is
# (re)built by content.search's post_migrate signal, which authenticates with
# the API key created just above -- so the migrate that ran before provision
# (when the key didn't exist yet) failed soft and skipped it. Re-running migrate
# here, with the key present, reconciles the index; reindex_studio then
# populates it. Both are CMS commands, so override the settings module for them
# (provision otherwise runs as LMS).
DJANGO_SETTINGS_MODULE=openedx_site.settings_cms_dev ./manage.py migrate
DJANGO_SETTINGS_MODULE=openedx_site.settings_cms_dev ./manage.py reindex_studio
