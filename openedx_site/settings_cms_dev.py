import os

from cms.envs.devstack import *
from openedx.core.lib.derived import derive_settings

from .shared_settings_overrides_dev import *

# Ensure that reads and writes to FEATURES['<BLAH>'] match top-level settings <BLAH>,
# live-updating. The former is a deprecated syntax for the latter.
FEATURES = FeaturesProxy(globals())

# Host URLs and cross-domain cookie settings are shared with the LMS and live
# in shared_settings_overrides_dev.py; here we add only CMS-specific wiring.
ALLOWED_HOSTS.append("studio.local.openedx.io")
ALLOWED_HOSTS.append("studio.local.openedx.io:8001")
SITE_NAME = CMS_BASE

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

# @@TODO: Put this back when we are running from openedx-template-site
# instead of openedx-platform.
## /path/to/openedx-template-site/staticfiles
#STATIC_ROOT = Path(__file__).parent.parent / "staticfiles"
derive_settings(__name__)
