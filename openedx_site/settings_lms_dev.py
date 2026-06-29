from path import Path

from lms.envs.devstack import *
from openedx.core.lib.derived import derive_settings

from .shared_settings_overrides_dev import *

# Ensure that reads and writes to FEATURES['<BLAH>'] match top-level settings <BLAH>,
# live-updating. The former is a deprecated syntax for the latter.
FEATURES = FeaturesProxy(globals())

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
# Share the CSRF cookie across the parent domain too, so the Authn MFE on the
# apps.local.openedx.io subdomain and the LMS use a single, unambiguous
# csrftoken cookie (avoids host-only vs. domain duplicate-cookie mismatches).
CSRF_COOKIE_DOMAIN = "local.openedx.io"

# --- Authn micro-frontend (../frontend-app-authn) -------------------------
# Use the modern Authn MFE instead of the legacy LMS login page. The MFE runs
# on its own origin (apps.local.openedx.io:1999, a subdomain of the cookie
# domain set above), so the LMS must:
#   (a) redirect /login + /register to the MFE,
#   (b) trust the MFE origin for credentialed CORS and for CSRF, and
#   (c) allow the MFE as a post-login redirect target.
# Mirrors Tutor's generated dev config; see
# /Users/kyle/tutor-root/env/apps/openedx/settings/lms/development.py
AUTHN_MFE_ORIGIN = "http://apps.local.openedx.io:1999"

# (a) Redirect login/registration to the MFE. This toggle gates the redirect
# (see user_authn/toggles.py: should_redirect_to_authn_microfrontend).
ENABLE_AUTHN_MICROFRONTEND = True
AUTHN_MICROFRONTEND_URL = f"{AUTHN_MFE_ORIGIN}/authn"
AUTHN_MICROFRONTEND_DOMAIN = "apps.local.openedx.io/authn"

# (b)+(c) The MFE makes credentialed cross-origin calls to the LMS (CSRF token,
# login_session, user info), so whitelist its origin for CORS + CSRF and allow
# it as a redirect target. CORS_ORIGIN_WHITELIST is a tuple in devstack, so
# rebuild it as a list rather than appending.
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_INSECURE = True
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [AUTHN_MFE_ORIGIN]
CSRF_TRUSTED_ORIGINS.append(AUTHN_MFE_ORIGIN)
LOGIN_REDIRECT_WHITELIST.append("apps.local.openedx.io:1999")

# Serve runtime config to the MFE via the LMS config API at /api/mfe_config/v1,
# so micro-frontends fetch their config from the LMS at startup rather than
# baking it in at build time (off by default in the platform). Low cache
# timeout per Tutor's note: the view is cheap and a long timeout causes
# stale-config bugs.
ENABLE_MFE_CONFIG_API = True
MFE_CONFIG_API_CACHE_TIMEOUT = 1
MFE_CONFIG.update({
    "BASE_URL": "apps.local.openedx.io",
    "LMS_BASE_URL": LMS_ROOT_URL,
    "LOGIN_URL": f"{LMS_ROOT_URL}/login",
    "LOGOUT_URL": f"{LMS_ROOT_URL}/logout",
    "CSRF_TOKEN_API_PATH": "/csrf/api/v1/token",
    "REFRESH_ACCESS_TOKEN_ENDPOINT": f"{LMS_ROOT_URL}/login_refresh",
    "ACCESS_TOKEN_COOKIE_NAME": "edx-jwt-cookie-header-payload",
    "USER_INFO_COOKIE_NAME": "user-info",
    "LANGUAGE_PREFERENCE_COOKIE_NAME": "openedx-language-preference",
    "MARKETING_SITE_BASE_URL": LMS_ROOT_URL,
    "SITE_NAME": "Open edX",
})

# Disable enterprise integration. Without this, the post-login redirect calls
# the Enterprise API at the devstack-default internal URL (localhost:18000),
# which isn't running here, and login 500s. We don't use enterprise features.
ENABLE_ENTERPRISE_INTEGRATION = False
if "enterprise.SystemWideEnterpriseUserRoleAssignment" in SYSTEM_WIDE_ROLE_CLASSES:
    SYSTEM_WIDE_ROLE_CLASSES.remove("enterprise.SystemWideEnterpriseUserRoleAssignment")

# @@TODO: Put this back when we are running from openedx-template-site
# instead of openedx-platform.
## /path/to/openedx-template-site/staticfiles
#STATIC_ROOT = Path(__file__).parent.parent / "staticfiles"

derive_settings(__name__)
