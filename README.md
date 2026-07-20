Warning: This doesn't entirely work yet. Issues:

* Assumes openedx-platform is cloned as a sibling directory.
* Not fully tested.

```
# Install prereqs for running on Ubuntu.
# If you don't trust this script or are running on a different system,
# then read through it and install the prereqs in your preferred way.
sudo ./install-ubuntu-prereqs.sh

# Create a venv using your preferred method
uv venv --python python3.12

# Get env vars (also sources .venv, if you put it there)
source ./env

# Install backend base+dev python deps
uv sync . --extra development

# Set up new frontends
git clone git@github.com:openedx/frontend-template-site frontend
nvm install
(cd frontend && npm ci)

# Build legacy frontends
# (requires node, which you installed in the previous step)
openedx_platform_npm ci
openedx_platform_npm run build # or build-dev


# Provision data
docker compose -d up
./provision.sh  # includes migrations
docker compose down  # if you're done

# Whenever you want to run it:
# In four different shells:
docker compose up
./manage.py runserver  # LMS
(source env_cms && ./manage.py runserver) # CMS
(cd frontend && npm dev:packages)  # Frontends
```

## Operating your site with Open edX Site Buddy

Running this site in [Claude Code](https://claude.com/claude-code)? Type
`/site-buddy` to bring up **Open edX Site Buddy** — an assistant for day-to-day
admin tasks (changing settings, and more over time) that explains every command
it runs as it goes.
