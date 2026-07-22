# Search (Meilisearch)

*A living write-up of how Meilisearch is set up for Studio content search +
tagging (and course search), and the non-obvious gotchas.*

Status: working as of this writing. Powers the authoring MFE's search/tagging.
Reference: tutor / tutor-mfe. Set up with the same compose+env_vars pattern as
mysql/mongo.

## Pieces

- **compose.yml** — a `meilisearch` service (`getmeili/meilisearch`), port 7700,
  `env_file: env_vars` (reads `MEILI_MASTER_KEY`, `MEILI_NO_ANALYTICS`).
  Data is not persisted to a named volume — it lives in the
  container and is lost on `docker compose down`.
- **env_vars** — `MEILI_MASTER_KEY` (server admin key, also read by the
  container), `MEILISEARCH_API_KEY_UID` (fixed UUIDv4 for the backend key),
  `MEILISEARCH_INDEX_PREFIX`.
- **shared_settings_overrides_dev.py** — `MEILISEARCH_ENABLED = True`,
  `SEARCH_ENGINE`, `MEILISEARCH_URL`/`MEILISEARCH_PUBLIC_URL` (both
  `http://localhost:7700` in this single-host dev setup), `MEILISEARCH_API_KEY`
  (derived — see below).
- **provision.sh** — creates the backend API key, reconciles the index, and
  populates it.
- **settings_lms_dev.py** — turns on the authoring MFE search/tagging flags in
  `MFE_CONFIG` (`MEILISEARCH_ENABLED`, `ENABLE_TAGGING_TAXONOMY_PAGES`, …).

## Gotcha 1: the API key value is derived, not chosen

The backend authenticates with `MEILISEARCH_API_KEY`, and at runtime the
platform looks that key up *by value* to get its UID and mint per-user tenant
tokens for the browser (`content/search/api.py`: `get_key(MEILISEARCH_API_KEY)`).
So the key must be a **real key that exists in Meilisearch** — the master key
won't work (it isn't a listed key, so the lookup 404s and browser search
breaks).

Meilisearch derives a key's value deterministically:
`value = HMAC_SHA256(master_key, uid)` (hex). So we don't store the key value;
we store the master key + a fixed UID, `provision.sh` creates the key with that
UID, and the settings compute the identical value. (Verified: the computed value
equals what Meilisearch returns.)

## Gotcha 2: the index is created by `post_migrate`, and needs the key first

Index creation/configuration (including the required `primaryKey`) happens in a
`post_migrate` signal handler (`content/search/handlers.py`), i.e. on
`./manage.py cms migrate`. `reindex_studio` only *populates* an existing index.
If you populate an index that was never reconciled, it gets created without a
primary key and Meilisearch errors:

> The primary key inference failed as the engine found N fields ending with `id`.

The handler authenticates with the API key and **fails soft** (logs a warning,
doesn't abort migrate) if the key is missing or Meilisearch is down. Our setup
order (`migrate` → `provision.sh`) means the first migrate runs before the key
exists, so it skips reconciliation. Therefore `provision.sh`, after creating the
key, re-runs `cms migrate` (reconciles the index with the key present) and then
`reindex_studio` (populates). Re-running migrate is idempotent.

So the correct order is always: **API key → `cms migrate` (create index) →
`reindex_studio` (populate)**.

## Notes

- `MEILISEARCH_PUBLIC_URL` is what the browser hits directly for search; the
  backend hands the MFE a tenant-scoped token + this URL. `localhost:7700`
  works from the browser here; Meilisearch's permissive CORS allows the MFE
  origin.
- Content created/imported later is indexed automatically via signals (as long
  as `MEILISEARCH_ENABLED`); `reindex_studio` is for bulk/initial population.
- Because Meilisearch data is ephemeral (no volume), after `docker compose down`
  re-run `provision.sh` to recreate the key + index.
