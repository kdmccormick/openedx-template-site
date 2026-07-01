# Running micro-frontends (MFEs) against this setup

*A living write-up of how we wire Open edX MFEs (all built on
`@edx/frontend-platform`) into this dev deployment, and the non-obvious gotchas.*

Status: authn, learning, and authoring MFEs wired and working (auth-wise) as of
this writing. See also `authn-mfe-login.md` (LMS login) and `studio-sso-login.md`
(Studio SSO).

## The MFEs we run (dev)

Each is served by its own `npm run dev` on a subdomain of the shared parent
domain `local.openedx.io`, under a `/<name>` public path:

| MFE | repo | URL |
|-----|------|-----|
| Authn | `frontend-app-authn` | `http://apps.local.openedx.io:1999/authn` |
| Learning | `frontend-app-learning` | `http://apps.local.openedx.io:2000/learning` |
| Authoring | `frontend-app-authoring` | `http://apps.local.openedx.io:2001/authoring` |

"Authoring" was historically the "course authoring" MFE (hence the
`COURSE_AUTHORING_MICROFRONTEND_URL` setting name); it now handles *all*
authoring, including libraries. There is no separate "library authoring" MFE.

## Runtime config comes from the LMS

Each MFE's `npm run dev` sets `MFE_CONFIG_API_URL=http://localhost:8000/api/mfe_config/v1`,
so the MFE fetches its runtime config from the **LMS** at startup, and that
config is merged *over* the MFE's build-time `.env`. Consequences:

- We enable `ENABLE_MFE_CONFIG_API` on the LMS and populate `MFE_CONFIG` there
  (LMS/Studio base URLs, login/logout URLs, cookie names, per-MFE URLs like
  `LEARNING_BASE_URL`). Editing an MFE's `.env` is usually unnecessary — set it
  in the LMS `MFE_CONFIG`.
- The config fetch hits the LMS with `Host: localhost:8000`; the LMS
  `ALLOWED_HOSTS` allows it (`*` in devstack).

## Auth model: shared cookies across subdomains

MFEs authenticate using JWT cookies minted by the LMS, not their own sessions:

1. The user logs in at the LMS (via the Authn MFE).
2. An authenticated MFE calls the LMS `REFRESH_ACCESS_TOKEN_ENDPOINT`
   (`/login_refresh`) to get a fresh JWT.
3. `frontend-auth` reads the access token from the JS-readable
   `edx-jwt-cookie-header-payload` cookie.

For step 3 to work across subdomains, the relevant cookies must be scoped to
the **parent** domain (`local.openedx.io`), not host-only, so an MFE on
`apps.local.openedx.io` can read/send them. Three cookie-domain settings, all
set to `local.openedx.io` in `shared_settings_overrides_dev.py`:

- `SESSION_COOKIE_DOMAIN` — the IDA session cookies (`lms_sessionid`,
  `studio_sessionid` — distinct names, so they don't collide).
- `CSRF_COOKIE_DOMAIN` — the CSRF cookie.
- **`SHARED_COOKIE_DOMAIN`** — the JWT auth cookies (`edx-jwt-cookie-*`). This
  is the one that bites you.

### Gotcha: `SHARED_COOKIE_DOMAIN` derives to None

Upstream defines `SHARED_COOKIE_DOMAIN = Derived(lambda s: s.SESSION_COOKIE_DOMAIN)`.
But the devstack import resolves that `Derived` **while `SESSION_COOKIE_DOMAIN`
is still `None`**, baking in `None`; overriding `SESSION_COOKIE_DOMAIN` afterward
does *not* re-trigger it. The symptom is subtle: login succeeds, sessions work
(you can reach `/admin`), the *unauthenticated* Authn MFE works — but any
*authenticated* MFE dies with:

> `[frontend-auth] Access token is still null after successful refresh.`

because `/login_refresh` returns 200 and sets `edx-jwt-cookie-header-payload`
host-only on `local.openedx.io`, which the MFE on `apps.local.openedx.io` can't
read. Fix: set `SHARED_COOKIE_DOMAIN` explicitly (we set it to
`SESSION_COOKIE_DOMAIN`).

This is a good example of the general trap: `Derived(...)` settings that depend
on values we override are resolved at devstack-import time against the *old*
value. When overriding such a base setting, set its dependents explicitly too.
(`LEARNING_MICROFRONTEND_NETLOC`, computed from `LEARNING_MICROFRONTEND_URL` at
import time, is the same kind of thing.)

## CORS / CSRF / redirect whitelisting

MFEs make credentialed cross-origin calls to the IDAs, so each IDA must:

- **CORS**: `CORS_ALLOW_CREDENTIALS = True`, `CORS_ORIGIN_ALLOW_ALL = False`
  (credentialed CORS is incompatible with allow-all), and the MFE origins in
  `CORS_ORIGIN_WHITELIST`.
- **CSRF**: MFE origins in `CSRF_TRUSTED_ORIGINS` (for their POST/PUT/DELETE).
- **Redirects**: MFE hosts in `LOGIN_REDIRECT_WHITELIST`.

To keep this DRY, `shared_settings_overrides_dev.py` defines `MFE_ORIGINS`
(full origins) and `MFE_HOSTS` (host:port), and sets `CORS_ORIGIN_WHITELIST` to
`MFE_ORIGINS`. CSRF/redirect whitelisting is a list *mutation*, so it's done
per-system in `settings_{lms,cms}_dev.py` (`CSRF_TRUSTED_ORIGINS += MFE_ORIGINS`,
`LOGIN_REDIRECT_WHITELIST += MFE_HOSTS`). Both IDAs whitelist the full set;
whitelisting an origin an IDA never hears from is harmless.

Note CMS devstack leaves `CORS_ORIGIN_WHITELIST` unset and defaults
`CORS_ORIGIN_ALLOW_ALL = True`; our `ALLOW_ALL = False` override makes a
whitelist mandatory, which the shared `CORS_ORIGIN_WHITELIST` supplies.

## Checklist: adding another MFE

1. Add its origin to `MFE_ORIGINS` in `shared_settings_overrides_dev.py`
   (handles CORS on both IDAs + CSRF/redirect via the per-system `+=`).
2. Point the owning IDA's URL setting at our host (e.g.
   `LEARNING_MICROFRONTEND_URL`, `COURSE_AUTHORING_MICROFRONTEND_URL`) and add
   any `MFE_CONFIG` entries the MFE reads (e.g. `LEARNING_BASE_URL`). Watch for
   `Derived`/import-time-computed dependents (see the gotcha above).
3. Run it with `npm run dev` (serves on its `apps.local.openedx.io:<port>/<path>`
   and pulls config from the LMS config API).
4. Test in a fresh window after any cookie-domain change.
