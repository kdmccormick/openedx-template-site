# Studio (CMS) login via OAuth2 SSO against the LMS

*A living write-up of how Studio authenticates in this setup, and the dev
settings that make it work.*

Status: working as of this writing. Settings live in
`openedx_site/settings_cms_dev.py` (CMS) and `provision.sh`; shared bits are in
`openedx_site/shared_settings_overrides_dev.py`. Reference for known-good
values: Tutor's generated `…/env/apps/openedx/settings/cms/development.py`.

## The model: LMS is the auth provider, CMS consumes it

Studio does **not** authenticate users itself. It logs users in against the LMS
using the `social-auth` `edx-oauth2` backend (an OAuth2 authorization-code
flow). Hitting a Studio page while logged out kicks off:

1. Studio redirects the browser to the LMS to start the OAuth2 flow.
2. If you have no LMS session, the LMS logs you in (via the Authn MFE — see
   `authn-mfe-login.md`).
3. The LMS redirects back to Studio's `/complete/edx-oauth2/` with an auth code.
4. Studio exchanges the code for a token **server-to-server** against the LMS,
   then establishes its own session.

Two consequences: getting LMS login working is a prerequisite, and the flow
needs both halves of an OAuth2 client to line up (below).

## The two halves of the OAuth2 client

For SSO to work, a registered client must exist in **two** places with matching
credentials:

- **In the LMS database** — a django-oauth-toolkit (DOT) "Application" with a
  client id/secret, the `authorization-code` grant, and the Studio redirect URI
  `http://studio.local.openedx.io:8001/complete/edx-oauth2/`. Created
  idempotently by `provision.sh` via `manage.py create_dot_application`
  (`--update`), owned by a dedicated `cms` service user.
- **In the CMS settings** — `SOCIAL_AUTH_EDX_OAUTH2_KEY` / `_SECRET` presenting
  the same credentials.

To keep these in sync there's a single source of truth: `CMS_SSO_OAUTH2_KEY`
and `CMS_SSO_OAUTH2_SECRET` in `env_vars`, read by both `provision.sh` (LMS
env) and `settings_cms_dev.py` (CMS env). If they ever drift, SSO fails with an
invalid-client/invalid-secret error.

## CMS settings that matter

- `SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT` — the **server-to-server** endpoint Studio
  calls to swap the code for a token. Must be an LMS URL reachable from the
  Studio process (`http://local.openedx.io:8000` here; resolves to localhost).
- `SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT` — where the **browser** is sent for
  the authorize step (the LMS, same URL in this single-host setup).
- `SOCIAL_AUTH_REDIRECT_IS_HTTPS = False` — we're on plain HTTP in dev.
- `FRONTEND_LOGIN_URL` / `FRONTEND_REGISTER_URL` — point at the LMS
  `/login` and `/register`.
- `SESSION_COOKIE_NAME` — CMS devstack already uses `studio_sessionid`, distinct
  from the LMS's `lms_sessionid`. This matters because both cookies live on the
  shared parent domain (`local.openedx.io`); a shared *name* would collide.

The cross-domain cookie settings (parent-domain `SESSION_COOKIE_DOMAIN` /
`CSRF_COOKIE_DOMAIN`, `SameSite=Lax`, non-Secure) are shared with the LMS in
`shared_settings_overrides_dev.py`.

## Testing

```
source env && ./provision.sh        # creates the cms user + DOT app in the LMS DB
# (LMS must be running for the SSO flow; MySQL must be up for provisioning)
source env_cms && ./manage.py runserver studio.local.openedx.io:8001
```

Then visit Studio in a fresh window. Note: `studio.local.openedx.io:8001/` may
redirect to the authoring MFE (`frontend-app-authoring`); if that MFE isn't
running, test the SSO flow against `…/admin` instead, which is served directly
by Studio.

## Gotchas

- **Redirect URI mismatch.** The DOT app's `--redirect-uris` must exactly match
  `http://studio.local.openedx.io:8001/complete/edx-oauth2/` (backend name
  `edx-oauth2`). A mismatch fails the callback.
- **`URL_ROOT` unreachable.** If the Studio process can't reach the LMS at
  `SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT`, the token exchange fails after the browser
  round-trip looks fine.
