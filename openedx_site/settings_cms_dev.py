import os

from cms.envs.devstack import *
from openedx.core.lib.derived import derive_settings

from .shared_settings_overrides_dev import *

# Ensure that reads and writes to FEATURES['<BLAH>'] match top-level settings <BLAH>,
# live-updating. The former is a deprecated syntax for the latter.
FEATURES = FeaturesProxy(globals())

# TODO comment and do same in lms
ROOT_URLCONF = "openedx_site.urls_cms"

point_caches_at_memcache(CACHES)

# Host URLs and cross-domain cookie settings are shared with the LMS and live
# in shared_settings_overrides_dev.py; here we add only CMS-specific wiring.
ALLOWED_HOSTS.append("studio.local.openedx.io")
ALLOWED_HOSTS.append("studio.local.openedx.io:8001")
SITE_NAME = CMS_BASE

# Our provisioning app (data migrations for waffle flags etc.). Installed in
# both LMS and CMS; the shared DB means each migration runs once.
INSTALLED_APPS.append("openedx_site.openedx_provisioning")

# --- Authenticate against the LMS via OAuth2 SSO --------------------------
# Studio does not authenticate users itself: it uses the social-auth edx-oauth2
# backend (already in AUTHENTICATION_BACKENDS) to log in against the LMS. The
# client id/secret must match the DOT application registered in the LMS DB by
# provision.sh; they're sourced from env_vars so there's a single source.
SOCIAL_AUTH_EDX_OAUTH2_KEY = os.environ["CMS_SSO_OAUTH2_KEY"]
SOCIAL_AUTH_EDX_OAUTH2_SECRET = os.environ["CMS_SSO_OAUTH2_SECRET"]
# URL_ROOT is the server-to-server endpoint Studio uses to exchange the auth
# code for a token; PUBLIC_URL_ROOT is where the browser is redirected. Both
# are the LMS, reachable at the same URL in this single-host dev setup.
SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT = LMS_ROOT_URL
SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT = LMS_ROOT_URL
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False  # scheme is included in the redirect_uri

# Send unauthenticated users to the LMS login/registration pages.
FRONTEND_LOGIN_URL = LMS_ROOT_URL + "/login"
FRONTEND_REGISTER_URL = LMS_ROOT_URL + "/register"

# --- Authoring MFE (../frontend-app-authoring) ----------------------------
# Studio redirects course-authoring pages to this MFE (formerly the "course
# authoring" MFE; all authoring, including libraries, now lives here). The MFE
# makes credentialed calls back to Studio, so trust MFE origins for CSRF and
# allow them as redirect targets. (CORS whitelisting of MFE_ORIGINS is shared;
# see shared_settings_overrides_dev.py. The MFE pulls its runtime config from
# the LMS MFE config API, so its URLs are configured there.)
COURSE_AUTHORING_MICROFRONTEND_URL = "http://apps.local.openedx.io:2001/authoring"
CSRF_TRUSTED_ORIGINS += MFE_ORIGINS
LOGIN_REDIRECT_WHITELIST += MFE_HOSTS

# @@TODO: Put this back when we are running from openedx-template-site
# instead of openedx-platform.
## /path/to/openedx-template-site/staticfiles
#STATIC_ROOT = Path(__file__).parent.parent / "staticfiles"
derive_settings(__name__)
