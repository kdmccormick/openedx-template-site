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