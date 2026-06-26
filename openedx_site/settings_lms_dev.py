from path import Path

from lms.envs.devstack import *
from openedx.core.lib.derived import derive_settings

from .shared_settings_overrides_dev import *

ALLOWED_HOSTS.append("local.openedx.io")
ALLOWED_HOSTS.append("local.openedx.io:8000")

# @@TODO: Put this back when we are running from openedx-template-site
# instead of openedx-platform.
## /path/to/openedx-template-site/staticfiles
#STATIC_ROOT = Path(__file__).parent.parent / "staticfiles"

derive_settings(__name__)
