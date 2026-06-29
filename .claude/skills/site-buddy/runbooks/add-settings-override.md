# Runbook: Add a Django settings override

> **Scope: dev only.** This site currently has just *dev* settings modules.
> When production settings are supported, this runbook will be reworked — tell
> the operator that any override added here applies to their **dev** site only.

Use this when the operator wants to change or override a Django setting for
their site (e.g. a feature flag, an email backend, an allowed host).

## Step 1 — Decide which file it goes in

Ask the operator (or infer from the setting) whether it applies to both
services or just one:

- **Both the LMS and the CMS (Studio)?**
  → `openedx_site/shared_settings_overrides_dev.py`
- **Just the LMS?**
  → `openedx_site/settings_lms_dev.py`
- **Just the CMS / Studio?**
  → `openedx_site/settings_cms_dev.py`

If you're not sure whether a setting is LMS-only, CMS-only, or shared, ask the
operator rather than guessing.

## Step 2 — Add the override

- Write the override as normal Python (assignment, or `.append(...)` /
  `.update(...)` if you're extending a list or dict the base config already
  defines).
- **Always precede it with a comment explaining *why* the override exists** —
  the problem it solves or the behavior it changes — not just what it sets.
- **Placement in `settings_lms_dev.py` / `settings_cms_dev.py`:** add your
  override *above* the `derive_settings(__name__)` call at the bottom. That call
  must stay last so derived settings pick up your change.
- In `shared_settings_overrides_dev.py`, just add it at the end of the file.

Example shape:

```python
# Operators behind a custom domain need it trusted for login POSTs, or
# Django rejects the CSRF Origin and silently bounces them to the login page.
CSRF_TRUSTED_ORIGINS.append("https://courses.example.com")
```

## Step 3 — Apply it (per your mode)

Editing a settings file is a write, so it depends on your mode:

- **Advice-only:** don't edit. Show the operator the exact change and which file
  it goes in, so they can make it themselves.
- **Pairing:** show the diff you're about to make and get a "yes" before writing.
- **Autonomous:** make the edit, then tell them what you changed and where.

## Step 4 — Make it take effect

Settings are read when a service starts. After the edit, the affected
`./manage.py runserver` process(es) need to reload:

- Django's `runserver` autoreloader usually restarts on a `.py` change on its
  own — have the operator glance at that terminal to confirm it reloaded.
- If it didn't, they should stop (`Ctrl-C`) and restart the affected
  server(s): the LMS, the CMS, or both, matching where you put the override.

Then have them verify the new behavior on the running site.
