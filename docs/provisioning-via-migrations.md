# Provisioning: what can move from provision.sh into migrations?

*Discovery notes on moving database provisioning out of the downstream-locked
`provision.sh` and into standard Django data migrations / `post_migrate`
reconciliation inside `openedx_site`.*

**Status:** the `openedx_site.openedx_provisioning` app now exists and carries
the first data migration — waffle flags/switches (see
`waffle-flags-tutor-vs-upstream.md` for the cross-reference). Other items
(DOT app, service users, etc.) remain candidates per the analysis below.

## The question

`provision.sh` currently does a mix of things after `migrate`. We expect to add
more (many waffle flags; maybe more DOT apps, service users, a demo course).
How much of that can be expressed as **Django migrations** (declarative,
idempotent, version-controlled, run automatically by `migrate`, and using the
same mechanism upstream uses) instead of a bash script only this repo can run?

## Precedent: upstream already does this

Open edX sets config via data migrations in the platform itself:

- **Waffle flags by default** — e.g.
  `cms/djangoapps/contentstore/migrations/0005_add_enable_checklists_quality_waffle_flag.py`
  and `.../0011_enable_markdown_editor_flag_by_default.py`,
  `lms/djangoapps/grades/migrations/0018_add_waffle_flag_defaults.py`. The
  pattern:

  ```python
  def create_flag(apps, schema_editor):
      Flag = apps.get_model('waffle', 'Flag')
      Flag.objects.get_or_create(name=..., defaults={'everyone': True})

  class Migration(migrations.Migration):
      dependencies = [('contentstore', '000x_...'), ('waffle', '0001_initial')]
      operations = [migrations.RunPython(create_flag, reverse_code=migrations.RunPython.noop)]
  ```

- **A service user** —
  `lms/djangoapps/commerce/migrations/0001_data__add_ecommerce_service_user.py`
  reads `settings.ECOMMERCE_SERVICE_WORKER_USERNAME`, does
  `get_or_create` + `set_unusable_password`, and depends on
  `swappable_dependency(settings.AUTH_USER_MODEL)`.

- **Seed data generally** — embargo countries, system-wide roles, tagging
  taxonomies, etc. all ship as `RunPython` data migrations.

So "provision via migration" is idiomatic, not a hack. Notably, a migration can
read `settings`, so a *generic* migration can produce *deployment-specific* rows.

## Prerequisite: make openedx_site an app

`openedx_site` is currently a settings/urls package, not an installed app (no
`AppConfig`, not in `INSTALLED_APPS`), so it can't hold migrations. To host
them we'd add a small app — e.g. `openedx_site.provisioning` with an
`AppConfig` and a `migrations/` package — and append it to `INSTALLED_APPS` in
the shared settings. LMS and CMS share one MySQL DB, so each migration runs
once (tracked in `django_migrations`) regardless of which system migrates first;
the app just needs to be installed in both.

## Two mechanisms

**(A) Data migrations (`RunPython`).** Run once, tracked, ordered via
`dependencies`. Best for stable seed data. Downsides: you must declare a
dependency on each target app's table-creating migration (e.g.
`('waffle','0001_initial')`), and every new flag is a new migration file.

**(B) `post_migrate` signal handler** in the app's `AppConfig`. Runs after
*all* migrations on every `migrate`, so all tables exist (no dependency
declaration) and it self-heals. Must be idempotent. This is exactly how the
platform reconciles the Meilisearch index today
(`content/search/handlers.py`), and it matches Tutor's init model, which is
"create if not already defined" run on every deploy.

Rule of thumb: **static defaults → data migration** (version history, upstream-
native); **desired-state that should track settings or self-heal → post_migrate**.

## Item-by-item

| provision item | DB-only? | Fits a migration? | Notes |
|---|---|---|---|
| **Waffle flags/switches** | yes (`waffle.Flag/Switch`) | **Yes — best candidate** | Direct upstream precedent. `apps.get_model('waffle',...)`, `get_or_create`, reverse=noop. Bulk of future provisioning. |
| **CMS SSO DOT app** | yes (`oauth2_provider.Application`) | **Yes, with a caveat** | Read id/secret/redirect from `settings` and `get_or_create`/update. Caveat: DOT may **hash** `client_secret`; a historical `apps.get_model` won't run the hashing logic, so prefer a `post_migrate` reconciler using the real model (or the `create_dot_application` code path). Bonus: keeps the app in sync with the CMS settings automatically. |
| **cms/service users** | yes (`auth_user`) | **Yes** | Precedent (commerce). Unusable-password service users are generic. |
| **Dev superuser (openedx/openedx)** | yes | technically, but **keep in provision** | Known dev password = environment-specific secret; not something to bake into a shared/upstreamable migration. |
| **openedx-authz `load_policies`** | yes (casbin rows) | maybe (`post_migrate`) | It's an idempotent mgmt command; upstream may fold it into post_migrate. Low priority. |
| **Meilisearch API key** | no (Meilisearch HTTP API) | **No — provision** | External service, not the DB. |
| **Meili index reconcile** | no | already automatic | Done by `content/search` post_migrate on `cms migrate`. |
| **reindex_studio / reindex_course** | no (Celery population) | **No — provision** | Operational, not schema/seed. |
| **Demo course import** | no (modulestore/Mongo + files) | **No — provision/seed step** | Heavy and stateful; running it in a migration is an anti-pattern. |

## Gotchas

- Use `apps.get_model('app','Model')` (historical models) in `RunPython`, not
  direct imports — except for `settings`/`get_user_model()` reads as commerce
  does. Historical models are bare: **custom `save()`/hashing does not run**
  (the DOT secret caveat above).
- Make everything idempotent (`get_or_create`/`update_or_create`) and use
  `reverse_code=RunPython.noop` for config you don't want dropped on rollback.
- Declare `dependencies` on the table-creating migration of each app you touch
  (`waffle`, `oauth2_provider`, `swappable_dependency(AUTH_USER_MODEL)`); when
  "must run after everything" is easier than pinning, use `post_migrate`.
- Migrations run at `migrate` time — *before* `provision.sh` in our README —
  which is a plus: e.g. the DOT app and flags would exist immediately, removing
  ordering fragility (cf. the Meilisearch key-before-migrate dance).

## Recommendation

Create one `openedx_site.provisioning` app that carries:

1. **Data migrations** for waffle flag/switch defaults (the big win; grows as we
   add flags) and other stable seed rows.
2. **A `post_migrate` reconciler** for settings-derived records that should stay
   in sync — chiefly the **CMS SSO DOT app** (sidesteps the secret-hashing
   caveat and keeps it aligned with `settings_cms_dev.py`), and optionally the
   `cms` service user.

Then `provision.sh` shrinks to only what genuinely can't be a migration:
the **dev superuser** (dev secret), the **Meilisearch API key** (external
service), **reindex** (Celery), and **demo-course import** (heavy/stateful).

This aligns with the repo's stated vision (a standard Django *project* that
installs openedx-platform as reusable apps): provisioning becomes declarative
Django data, most of it using the exact mechanism upstream already uses, rather
than logic trapped in a downstream-only shell script.

### Open questions

- Whether to install `openedx_site.provisioning` in prod too (flags/DOT app are
  prod-relevant) vs. a dev-only variant for dev-only rows.
- Per-flag values that differ by environment: read from `settings`, or keep a
  small declarative table (name → default) the migration iterates.
- Whether any of our flag defaults are generic enough to PR upstream to the
  owning app instead of carrying here.
