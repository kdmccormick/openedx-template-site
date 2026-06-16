Warning: This doesn't entirely work yet. Issues:

* Assumes openedx-platform is cloned as a sibling directory.
* Assumes openedx-platform is on this PR's branch: https://github.com/openedx/openedx-platform/pull/38769
* No frontends.
* Not fully tested.

```
# Create a venv using your preferred method
uv venv --python python3.12
source .venv/bin/activate

# Install deps
uv sync  # Or: `pip install .`

# Run supporting services
docker compose up

# Set shell environment vars.
# Can replace lms with lms_dev, cms_dev, or cms.
. ./env lms

./manage.py migrate
./manage.py runserver
```
