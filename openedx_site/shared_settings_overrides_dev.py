# This is not a root settings module itself, but it has a few
# settings overrides that we want consistent everwhere.

import hashlib
import hmac
import os
import warnings

from openedx.core.lib.derived import Derived
from openedx.envs.common import BLOCK_STRUCTURES_SETTINGS

# Repo root (this file lives in <repo>/openedx_site/). Computed from __file__
# rather than the CWD, because manage.py runs with CWD=../openedx-platform.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
# The JWT auth cookies (edx-jwt-cookie-*) use SHARED_COOKIE_DOMAIN, not
# SESSION_COOKIE_DOMAIN. Upstream defines it as Derived(SESSION_COOKIE_DOMAIN),
# but the devstack import resolves that Derived while SESSION_COOKIE_DOMAIN is
# still None, baking in None; our override above doesn't re-trigger it. Set it
# explicitly so the JS-readable access-token cookie is scoped to the parent
# domain and readable by MFEs on apps.local.openedx.io (otherwise frontend-auth
# reports "Access token is still null after successful refresh").
SHARED_COOKIE_DOMAIN = SESSION_COOKIE_DOMAIN

# CORS base flags. MFEs make credentialed cross-origin calls to the IDAs, which
# is incompatible with allow-all, so we whitelist specific origins below.
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_INSECURE = True

# MFE origins we run in dev. Both the LMS and the CMS whitelist the full set for
# CORS (harmless on an IDA that a given MFE doesn't call). CSRF-trust and
# login-redirect whitelisting are list *mutations* and so are done per-system
# (see settings_{lms,cms}_dev.py), using MFE_ORIGINS / MFE_HOSTS from here.
# Ports match tutor-mfe's canonical MFE roster. We configure the IDAs to talk
# to all of them; we don't have to run them all at once.
MFE_ORIGINS = [
    "http://apps.local.openedx.io:1984",  # frontend-app-communications
    "http://apps.local.openedx.io:1993",  # frontend-app-ora-grading
    "http://apps.local.openedx.io:1994",  # frontend-app-gradebook
    "http://apps.local.openedx.io:1995",  # frontend-app-profile
    "http://apps.local.openedx.io:1996",  # frontend-app-learner-dashboard
    "http://apps.local.openedx.io:1997",  # frontend-app-account
    "http://apps.local.openedx.io:1999",  # frontend-app-authn
    "http://apps.local.openedx.io:2000",  # frontend-app-learning
    "http://apps.local.openedx.io:2001",  # frontend-app-authoring
    "http://apps.local.openedx.io:2002",  # frontend-app-discussions
]
MFE_HOSTS = [origin.split("//", 1)[1] for origin in MFE_ORIGINS]  # "host:port"
CORS_ORIGIN_WHITELIST = list(MFE_ORIGINS)

# Course import unpacks the uploaded .tar.gz into a scratch dir under
# GITHUB_REPO_ROOT (upstream default: ENV_ROOT/data, which doesn't exist here).
# The importer uses os.mkdir (not makedirs), so a missing parent 500s the
# import. Point it at the repo-local tmp-data/, whose own .gitignore keeps the
# (otherwise-ignored) dir in the repo so it always exists -- no host mutation
# from settings needed.
GITHUB_REPO_ROOT = os.path.join(_REPO_ROOT, "tmp-data")

# Meilisearch (Studio content search + tagging, and course search). Runs in the
# compose stack on localhost:7700. MEILISEARCH_URL is used by the python backend;
# MEILISEARCH_PUBLIC_URL is what the browser hits directly (same host here). The
# backend authenticates with an API key whose value Meilisearch derives
# deterministically from the master key + the key's uid (HMAC-SHA256); we compute
# the same value here, and provision.sh creates the key with that uid. The
# platform then looks the key up by value to mint per-user tenant tokens for the
# browser (see content/search/api.py).
SEARCH_ENGINE = "search.meilisearch.MeilisearchEngine"
MEILISEARCH_ENABLED = True
MEILISEARCH_URL = "http://localhost:7700"
MEILISEARCH_PUBLIC_URL = "http://localhost:7700"
MEILISEARCH_INDEX_PREFIX = os.environ.get("MEILISEARCH_INDEX_PREFIX", "openedx_")
MEILISEARCH_API_KEY = hmac.new(
    os.environ["MEILI_MASTER_KEY"].encode(),
    os.environ["MEILISEARCH_API_KEY_UID"].encode(),
    hashlib.sha256,
).hexdigest()