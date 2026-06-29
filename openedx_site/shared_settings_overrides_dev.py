# This is not a root settings module itself, but it has a few
# settings overrides that we want consistent everwhere.

import warnings

from openedx.core.lib.derived import Derived
from openedx.envs.common import BLOCK_STRUCTURES_SETTINGS


# Silences a Swagger (API docs) depr warning that doesn't apply to us.
SWAGGER_USE_COMPAT_RENDERERS = False

# Silence spurious warning about missing STORAGE_CLASS key
BLOCK_STRUCTURES_SETTINGS["STORAGE_CLASS"] = None

# Silences a RemovedInDjango60Warning
FORMS_URLFIELD_ASSUME_HTTPS = True


# @@TODO warnings.filterwarnings doesn't work, and adjusting logging config
# seems to create worse problems.
#warnings.filterwarnings("ignore", message=".*casbin enforcer initialisation.*")
#def _adjust_logging(settings):
#    # Silence warning "Deferring casbin enforcer initialisation until django is ready"
#    settings.LOGGING["loggers"].setdefault("casbin_adapter", {})["level"] = "WARNING"
# adjust logging in a hacky way, because importing get_logging_config causes startup issues
#DUMMY_SETTING_TO_ADJUST_LOGGING = Derived(_adjust_logging)


# More warnings that are currently out of our control
warnings.filterwarnings("ignore", message="'imghdr' is deprecated", module="pgpy")
warnings.filterwarnings("ignore", message="urllib3.*or chardet.*doesn't match a supported version", module="requests")
warnings.filterwarnings("ignore", message="urllib3.*or chardet.*doesn't match a supported version", module="snowflake")
warnings.filterwarnings("ignore", message="ContentLibraryPermission model and related.*")


# --- Cross-cutting dev overrides ------------------------------------------
# NOTE: this module runs in its own namespace and does NOT import the lms/cms
# devstack settings, so it can only do *scalar assignments* here (the importing
# root module picks them up via `import *`, overriding the devstack defaults).
# List/dict *mutations* (.append/.update/.remove on settings like
# CSRF_TRUSTED_ORIGINS or SYSTEM_WIDE_ROLE_CLASSES) must live in the per-system
# settings_{lms,cms}_dev.py, where those names are in scope.

# Host URLs. The LMS is the auth provider; the CMS (Studio) consumes it. Both
# systems must agree on these, so they live here.
LMS_BASE = "local.openedx.io:8000"
LMS_ROOT_URL = "http://" + LMS_BASE
CMS_BASE = "studio.local.openedx.io:8001"
CMS_ROOT_URL = "http://" + CMS_BASE

# Cross-domain cookies. We serve over plain HTTP in dev, so cookies cannot be
# Secure; the base config's SameSite="None" requires Secure and would be
# dropped by browsers, so use "Lax". Scoping the session and CSRF cookies to
# the shared parent domain (rather than host-only) lets the LMS, CMS, and MFE
# subdomains share unambiguous cookies -- required for SSO. (The LMS and CMS
# use distinct cookie *names*, so the session cookies don't collide.)
SESSION_COOKIE_DOMAIN = "local.openedx.io"
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_DOMAIN = "local.openedx.io"
CSRF_COOKIE_SECURE = False

# CORS base flags. MFEs make credentialed cross-origin calls to the IDAs, which
# is incompatible with allow-all; each system whitelists specific origins.
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_INSECURE = True