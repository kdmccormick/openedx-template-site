from path import Path

from lms.envs.devstack import *
from openedx.core.lib.derived import derive_settings

from .shared_settings_overrides_dev import *

# Ensure that reads and writes to FEATURES['<BLAH>'] match top-level settings <BLAH>,
# live-updating. The former is a deprecated syntax for the latter.
FEATURES = FeaturesProxy(globals())

# We serve the LMS from local.openedx.io:8000 rather than the devstack default
# of localhost:18000. Host URLs and the cross-domain cookie settings are shared
# with the CMS and live in shared_settings_overrides_dev.py; here we add only
# the LMS-specific host wiring. Without trusting our real origin for CSRF and
# allowing it as a redirect target, the login POST 403s and bounces.
ALLOWED_HOSTS.append("local.openedx.io")
ALLOWED_HOSTS.append("local.openedx.io:8000")
SITE_NAME = LMS_BASE
CSRF_TRUSTED_ORIGINS.append(LMS_ROOT_URL)
LOGIN_REDIRECT_WHITELIST.append(LMS_BASE)

# --- Micro-frontends ------------------------------------------------------
# The MFEs run on their own origins (apps.local.openedx.io:<port>, subdomains
# of the cookie domain) and make credentialed cross-origin calls to the LMS, so
# trust every MFE origin for CSRF and allow it as a post-login redirect target.
# (CORS whitelisting of MFE_ORIGINS is shared; see shared_settings_overrides_dev.py.)
CSRF_TRUSTED_ORIGINS += MFE_ORIGINS
LOGIN_REDIRECT_WHITELIST += MFE_HOSTS

# Use the modern Authn MFE instead of the legacy LMS login page: redirect
# /login + /register to it. The redirect is gated on this toggle (see
# user_authn/toggles.py: should_redirect_to_authn_microfrontend).
ENABLE_AUTHN_MICROFRONTEND = True
AUTHN_MICROFRONTEND_URL = "http://apps.local.openedx.io:1999/authn"
AUTHN_MICROFRONTEND_DOMAIN = "apps.local.openedx.io/authn"

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
    # Studio + authoring MFE, so frontend-app-authoring (which pulls its config
    # from this API) talks to the right Studio rather than the devstack default.
    "STUDIO_BASE_URL": CMS_ROOT_URL,
    "COURSE_AUTHORING_MICROFRONTEND_URL": "http://apps.local.openedx.io:2001/authoring",
    "LEARNING_BASE_URL": "http://apps.local.openedx.io:2000/learning",
})

# Learning MFE (../frontend-app-learning): the LMS links learners to it for
# courseware. LMS-only; point it at our host (devstack default is
# localhost:2000). NETLOC is computed from the URL at devstack-import time, so
# it also needs updating.
LEARNING_MICROFRONTEND_URL = "http://apps.local.openedx.io:2000/learning"
LEARNING_MICROFRONTEND_NETLOC = "apps.local.openedx.io:2000"

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
