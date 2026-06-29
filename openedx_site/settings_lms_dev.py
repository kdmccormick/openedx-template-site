from path import Path

from lms.envs.devstack import *
from openedx.core.lib.derived import derive_settings

from .shared_settings_overrides_dev import *

ALLOWED_HOSTS.append("local.openedx.io")
ALLOWED_HOSTS.append("local.openedx.io:8000")

# We serve the LMS from local.openedx.io:8000 rather than the devstack
# default of localhost:18000. Point the host-derived settings at the real
# host so that login works: otherwise the login POST's Origin is not in
# CSRF_TRUSTED_ORIGINS and Django rejects it with a 403, silently bouncing
# the user back to the login page.
LMS_BASE = "local.openedx.io:8000"
LMS_ROOT_URL = "http://local.openedx.io:8000"
SITE_NAME = LMS_BASE
CSRF_TRUSTED_ORIGINS.append("http://local.openedx.io:8000")
LOGIN_REDIRECT_WHITELIST.append("local.openedx.io:8000")

# We serve over plain HTTP in dev, so cookies cannot be marked Secure.
# The base config uses SESSION_COOKIE_SAMESITE = "None" (for MFE/embedding,
# which assumes HTTPS), but browsers reject a SameSite=None cookie that is
# not also Secure -- so the session cookie gets silently dropped and login
# bounces back to the login page. Use "Lax" for HTTP dev, matching Tutor.
SESSION_COOKIE_DOMAIN = "local.openedx.io"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"

# Enable the MFE Config API at /api/mfe_config/v1 on the LMS. This lets our
# micro-frontends fetch their runtime configuration from the LMS at startup
# rather than baking it in at build time. Off by default in the platform.
ENABLE_MFE_CONFIG_API = True

# @@TODO: Put this back when we are running from openedx-template-site
# instead of openedx-platform.
## /path/to/openedx-template-site/staticfiles
#STATIC_ROOT = Path(__file__).parent.parent / "staticfiles"

derive_settings(__name__)
