# Getting login working via the Authn MFE

*A living write-up of the LMS dev-settings needed to log in through the modern
Authn micro-frontend (`frontend-app-authn`) in this non-Tutor setup.*

Status: working as of this writing. All of the settings below live in
`openedx_site/settings_lms_dev.py` (LMS dev). Reference for known-good values:
Tutor's generated `…/env/apps/openedx/settings/lms/development.py`.

## The setup

- LMS served at `http://local.openedx.io:8000`.
- Authn MFE served (via `npm run dev` in `../frontend-app-authn`) at
  `http://apps.local.openedx.io:1999/authn`.
- Plain HTTP, no proxy. The two run on different *ports* of subdomains of the
  shared parent domain `local.openedx.io`.

We deliberately diverge from devstack defaults, which assume the LMS lives at
`localhost:18000` and that supporting IDAs (enterprise, etc.) are reachable.

## The fixes, in the order we discovered them

Each of these was a distinct symptom; they had to be peeled back one at a time.

1. **Host-derived settings pointed at `localhost:18000`.**
   Set `LMS_BASE` / `LMS_ROOT_URL` / `SITE_NAME` to the real host, and add the
   real origin to `CSRF_TRUSTED_ORIGINS` and `LOGIN_REDIRECT_WHITELIST`.
   Symptom otherwise: login POST's Origin not trusted → 403 → silent bounce.

2. **`SESSION_COOKIE_SAMESITE = "None"` without `Secure`.**
   The base config uses `SameSite=None` (for MFE/embedding, which assumes
   HTTPS). On plain HTTP we can't set `Secure`, and browsers *reject* a
   `SameSite=None` cookie that isn't `Secure` — so the session cookie was
   silently dropped and login bounced. Fix: `SESSION_COOKIE_SAMESITE = "Lax"`,
   `SESSION_COOKIE_SECURE = False`, `CSRF_COOKIE_SECURE = False`.
   Tell-tale: works under `curl` (which ignores SameSite/Secure) but not in a
   browser.

3. **Legacy login page instead of the MFE.**
   Turn on the redirect to the Authn MFE and tell the LMS where it lives:
   `ENABLE_AUTHN_MICROFRONTEND = True`, `AUTHN_MICROFRONTEND_URL`,
   `AUTHN_MICROFRONTEND_DOMAIN`. The redirect is gated by
   `user_authn/toggles.py: should_redirect_to_authn_microfrontend()`, which
   reads `settings.FEATURES.get("ENABLE_AUTHN_MICROFRONTEND")`. (We write the
   *top-level* `ENABLE_AUTHN_MICROFRONTEND`; the `FeaturesProxy` keeps
   `FEATURES[...]` in sync — see below.)
   Bonus: the MFE uses the **v2** login endpoint, which accepts
   `email_or_username`, so username login works (the legacy v1 endpoint only
   resolved by email).

4. **CORS + MFE runtime config.**
   The MFE makes credentialed cross-origin calls to the LMS (CSRF token, login,
   user info), so whitelist its origin: `CORS_ORIGIN_ALLOW_ALL = False`,
   `CORS_ALLOW_CREDENTIALS = True`, and add the MFE origin to
   `CORS_ORIGIN_WHITELIST` (which is a *tuple* in devstack — rebuild it as a
   list, don't `.append`). Also serve runtime config via
   `ENABLE_MFE_CONFIG_API = True` + a populated `MFE_CONFIG`.

5. **CSRF token/cookie mismatch across subdomains.**
   `403 (CSRF token from the 'X-Csrftoken' HTTP header incorrect.)` — a token
   was sent and a cookie was present, but they didn't match (stale/duplicate
   cookie). Pin the CSRF cookie to the shared parent domain so the LMS and the
   `apps.` subdomain use one unambiguous cookie:
   `CSRF_COOKIE_DOMAIN = "local.openedx.io"` (mirroring
   `SESSION_COOKIE_DOMAIN`). **Clear cookies for `*.local.openedx.io` after
   changing cookie domains** or the old host-only cookies reproduce the error.

6. **Enterprise integration 500 on the post-login redirect.**
   After auth *succeeds*, the redirect logic calls the Enterprise API at the
   devstack-default internal URL (`localhost:18000`), which isn't running →
   `ConnectionError` → 500. We don't use enterprise: set
   `ENABLE_ENTERPRISE_INTEGRATION = False` and remove
   `enterprise.SystemWideEnterpriseUserRoleAssignment` from
   `SYSTEM_WIDE_ROLE_CLASSES`.

## Why the cookie *domain* matters

`SESSION_COOKIE_DOMAIN` and `CSRF_COOKIE_DOMAIN` are both set to
`local.openedx.io` (the parent), not left host-only. That scopes the session,
JWT, and CSRF cookies to `*.local.openedx.io`, so they're shared between the LMS
and the MFE subdomain. Ports don't matter for cookies, so the `:8000` vs `:1999`
split is irrelevant here.

## Feature toggles: top-level, not `FEATURES[...]`

Write toggles as top-level settings (`ENABLE_AUTHN_MICROFRONTEND = True`), not
`FEATURES["ENABLE_AUTHN_MICROFRONTEND"]` (deprecated, going away). The line
`FEATURES = FeaturesProxy(globals())` near the top of the settings module keeps
the two live-synced in both directions, so platform code that still reads
`settings.FEATURES.get(...)` keeps working. Without that proxy line, setting only
the top-level name does *not* reach `FEATURES` and silently breaks the toggle.

## Testing checklist

- `source env && ./manage.py …` (env must be sourced in the *same* command).
- Restart the LMS after settings changes.
- Use a fresh incognito window (or clear `*.local.openedx.io` cookies) when
  cookie-domain/CSRF settings change.
- Log in at `http://local.openedx.io:8000/login` with
  `openedx@local.openedx.io` (or username `openedx`) / `openedx`.
