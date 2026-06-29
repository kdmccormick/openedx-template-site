Warning: This doesn't entirely work yet. Issues:

* Assumes openedx-platform is cloned as a sibling directory.
* No frontends.
* Not fully tested.

```
# Create a venv using your preferred method
uv venv --python python3.12

# Get env vars (also sources .venv, if you put it there)
source env

# Install deps
uv pip install -r requirements_tmp.txt  # future: `uv sync .`

# Provision data
docker compose -d up
./manage.py migrate
./provision.sh
docker compose down  # if you're done

# Whenever you want to run it:
# In three different shells:
docker compose up
./manage.py runserver  # LMS
DJANGO_SETTINGS_MODULE=openex_site.settings_cms_dev ./manage.py runserver # CMS
```

## Operating your site with Open edX Site Buddy

Running this site in [Claude Code](https://claude.com/claude-code)? Type
`/site-buddy` to bring up **Open edX Site Buddy** — an assistant for day-to-day
admin tasks (changing settings, and more over time) that explains every command
it runs as it goes.
