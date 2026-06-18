# Static assets discovery (first pass)

Status: discovery notes, not a finalized plan. Context: openedx-site installs
openedx-platform as a non-editable package; static assets are missing from the
install (e.g. `./manage.py migrate` fails reading
`lms/static/images/default-badges/honor.png`).

## Root cause of the missing-assets / migration failure

`openedx-platform/pyproject.toml` declares almost no static as package data:

```toml
[tool.setuptools.package-data]
xmodule = ["js/module/*"]   # the entire list
```

The `static/` trees under `lms`, `cms`, `common`, `openedx` are NOT included,
so a non-editable install drops them. The failing badge PNGs are **checked-in
source files**, so that specific failure is fixable just by widening
`package-data` — independent of the JS/CSS build.

## `npm run build` decomposition

`npm run build` = `npm run webpack` + `npm run compile-sass`
(`package.json`). Plus `postinstall: scripts/copy-node-modules.sh` vendors node
deps into the source tree.

## Three layers of "static assets" (increasing difficulty)

1. **Source assets** — images, fonts, vendored JS, ~38 pre-existing `.css`.
   Already in git; need only `package-data` inclusion. Fixes the migration.
2. **Compiled CSS** — `scripts/compile_sass.py` output. Generated, gitignored,
   but written *into the app static source dirs* (see below).
3. **Webpack bundles + the collected `staticfiles` tree** — the hard layer;
   split further below.

## Where build artifacts actually land (verified)

Build outputs are written **into the app `static/` source dirs**, NOT into the
collected `staticfiles`/`STATIC_ROOT` tree:

| Output | Destination | In git? |
|---|---|---|
| Webpack JS bundles (`webpack.common.config.js` `output.path`) | `common/static/bundles` | gitignored |
| Default LMS Sass (`scripts/compile_sass.py`) | `lms/static/css` | gitignored |
| Certificate Sass | `lms/static/certificates/css` | gitignored |
| Default CMS Sass | `cms/static/css` | gitignored |
| `webpack-stats.json` / `webpack-worker-stats.json` (BundleTracker manifests) | `STATIC_ROOT_LMS`/`STATIC_ROOT_CMS` (collected dir) | — |

So only the small webpack **stats manifests** go to the collected dir; the
actual bundles + compiled CSS sit inside `common/static`, `lms/static`,
`cms/static`.

## How collectstatic sees them (verified, `openedx/envs/common.py`)

```python
STATICFILES_DIRS = [COMMON_ROOT/"static", PROJECT_ROOT/"static", XMODULE_ROOT/"static"]
STATICFILES_FINDERS = [theming finder, FileSystemFinder, AppDirectoriesFinder,
                       XBlockPipelineFinder, PipelineFinder]
```

`collectstatic` gathers `common/static`, `lms|cms/static`, `xmodule/static`, and
every installed app's `static/` dir into `STATIC_ROOT` (`staticfiles`, default
`ENV_ROOT/staticfiles`). It is a derived copy.

## Layer-3 split (working hypothesis — CONFIRMED)

- **Build artifacts** (compiled CSS, webpack bundles): an installer *cannot*
  regenerate these without invoking openedx-platform's internal Node/Sass build
  pipeline. They live inside the app `static/` dirs. → **We DO want to bundle
  these in the wheel** (run `npm run build` before packaging, include the
  generated dirs in `package-data`).
- **Collected `staticfiles` (`STATIC_ROOT`)**: this is the standard Django
  `./manage.py collectstatic` output — a copy of every source asset + build
  artifact into one servable tree. It is derived and reproducible by the
  installer. → **We do NOT bundle this**; the installer/deployer runs
  `collectstatic` themselves (into an ephemeral dir served by
  whitenoise/nginx/CDN). Bundling it would duplicate everything and is
  non-idiomatic.

## Rabbit holes noted, not yet explored

- `common/static` is ~109M (much legacy/vendored RequireJS-era JS) — may not
  want to ship wholesale.
- Build-before-package ordering: setuptools won't run `npm run build`; needs a
  build hook or a two-step CI (build, then `pip wheel`).
- Theming (`ThemeFilesFinder`, comprehensive themes) + `collectstatic` interplay.
- `node_modules/@edx` is inserted into `STATICFILES_DIRS` (`lms/envs/common.py`).

## Source dir sizes

| dir | size | tracked files |
|---|---|---|
| common/static | 109M | 1050 |
| openedx | 27M | 2099 |
| xmodule/js | 20M | 135 |
| lms/static | 15M | 774 |
| cms/static | 6.8M | 334 |
