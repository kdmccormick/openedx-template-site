# Static assets discovery (first pass)

*This is a living discovery written by Claude as we work through the challenge of getting openedx-platform static assets to be served through openedx-template-site.*

Status: discovery notes, not a finalized plan. Context: openedx-site installs
openedx-platform as a non-editable package; static assets are missing from the
install (e.g. `./manage.py migrate` fails reading
`lms/static/images/default-badges/honor.png`).

## CURRENT DECISION (supersedes the "bundle the build artifacts" leanings below)

We pivoted away from bundling the legacy *built* assets into the wheel, because
they are large (webpack `bundles` alone is 73M) and on track for deletion within
~a year. Three categories, not two:

1. **Legacy *built* assets** — webpack bundles + compiled Sass→CSS. Regenerable,
   gitignored, dying. → NOT shipped in the wheel.
2. **openedx-platform's own *source* static** — badge PNGs, fonts, images,
   vendor CSS, legacy JS/Sass *sources*. Checked into git; some required at
   runtime/migrate time (the badge PNG that started this is here). → SHIPPED.
3. **3rd-party app static** — from other pip packages; collected normally.

Resulting model:

- **Base wheel = Python + all checked-in *source* static, minus build outputs.**
  Expressed simply by NOT running `npm run build` before
  `python -m build --wheel` — the `"*" = ["static/**/*"]` glob only matches
  on-disk files, so gitignored build outputs are naturally absent. Drops the 73M
  bundles for free; `pip install` makes the badge migrate + source-asset
  `collectstatic` work.
- **Legacy built assets via a console script** shipped by openedx-platform
  (e.g. `build_legacy_openedx_platform_frontends`) that runs the existing
  `npm ci && npm run build[-dev]` pipeline in the install location, writing
  artifacts in-place. Opt-in; evaporates when legacy is deleted upstream.
- **Dev skips collectstatic** entirely (see dev workflow section). The
  "collectstatic depends on the build" knot is a PROD-only concern, parked for
  now (likely `PipelineFinder`/`webpack-stats.json` post-processing).

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

## Build-before-package ordering (layer 3, the hard part)

Context: openedx-platform is **not on PyPI**; today the canonical way to run it
is as a Django project invoked from source, and `pyproject.toml` exists mainly
to register entry points. Publishing a wheel is the new goal. Since it has never
been packaged, we are designing the release pipeline from scratch.

The asset build has both a Python and a Node dependency (because
`compile_sass.py` is a Python script):

- `pip install -r requirements/edx/assets.txt` (libsass etc.)
- node 24 (`.nvmrc`) + `npm ci` + `npm run build` (prod, not `build-dev`)

Pre-package sequence: **assets.txt → `npm ci` → `npm run build` → build wheel.**
(`collectstatic`/`migrate`/`runserver` are deploy/runtime, not packaging.)

setuptools will not run Node, so "build assets, then package" must be enforced
somewhere. Three options, increasing in magic:

- **A. Explicit release pipeline** (Makefile target + CI workflow): documented
  sequence, no backend magic. Risk: building a wheel without the asset step
  ships an empty one.
- **B. Verify-only build-backend shim** (CHOSEN, with A): a tiny in-tree PEP 517
  backend wrapping `setuptools.build_meta` whose `build_wheel` *asserts* the
  built artifacts exist (e.g. `common/static/bundles` non-empty, `lms/static/css`
  present) and raises otherwise. Does NOT run Node — no node requirement at
  wheel-build time — just refuses to produce a silently-broken wheel.
- **C. Build-running backend shim**: same wrapper but actually runs
  `npm ci && npm run build` in `build_wheel`. Fully enforcing even for
  `pip install .`, but requires Node 24 wherever a wheel is built and makes
  `pip install .` very heavy. Rejected as too much magic for the common case.

**Decision: A + B.** Deterministic pipeline plus a cheap guardrail.

Two follow-on decisions:

1. **Wheel-only vs. sdist** — under discussion (see separate section / team
   call). Build artifacts are gitignored, which interacts badly with the default
   sdist→wheel-from-sdist flow.
2. **`package-data` glob mechanics** — next deep-dive. setuptools attributes
   each file to its nearest enclosing package, and recursive `**` globs over
   deeply-nested static (esp. under `openedx/`) have sharp edges. Needs real
   wheel-build experimentation (`unzip -l`), not trust in the globs.

## Wheel-only vs. sdist

Two PyPI artifact types: **sdist** (source; consumer builds it into a wheel at
install time) and **wheel** (pre-built; unpacked as-is). openedx-platform is
pure Python, so its wheel is universal (`py3-none-any`) — no per-platform build
reason to need an sdist.

The sdist trap: `python -m build` (no args) builds the sdist first, then builds
the wheel *from the sdist*. The sdist is assembled from tracked/MANIFEST files,
but our build artifacts are **gitignored** → not in the sdist → wheel comes out
empty. A correct sdist would require either grafting built artifacts into a
"source" dist (backwards, foot-gun) or a self-building sdist (Node at install
time = option C). Neither is clean.

**Decision: wheel-only to start.** Build the wheel directly with
`python -m build --wheel` (or `pip wheel . --no-deps`), which builds from the
source tree and skips the sdist round-trip entirely. Pairs with the B shim
(guard `build_wheel`; `build_sdist` unsupported).

- Cost: no source artifact on PyPI; tooling that requires an sdist
  (`pip download` of sdist, some mirrors/distro/conda packagers) isn't served.
  For openedx-site we control the install, so this is a non-issue for our goal.
- Verify before org-wide adoption: Open edX uses hash-pinned requirements
  (pip-tools); confirm nothing assumes an sdist exists (hash-pinning itself
  works fine against wheels).
- This is a genuine upstream policy decision (wheel-only is slightly unusual) —
  raise with the team, don't just bake it in.

## Editable installs and the dev story (orthogonal to sdist)

`pip install -e path` is a THIRD install mode, not sdist and not wheel. Via
PEP 660 it installs a redirect so `import lms` resolves to the **live source
tree**; nothing is copied. So "no sdist" does NOT affect the dev story.

Dev loop (vision): `pip install -e ../openedx-platform`, then:
- Edit Python → reflected immediately (runserver autoreload).
- Edit JS/Sass → `npm run build-dev` (or `npm run watch`) regenerates artifacts
  in-place in the source `static/` dirs → served.

Works because build-dev writes artifacts into the same source tree that editable
points imports at.

Caveats:
- In editable mode the whole source dir is on the import path, so `package-data`
  globs are effectively bypassed — **editable dev can mask packaging bugs**.
  Mitigation: a CI job that builds the real wheel and smoke-tests it (e.g. runs
  the `migrate` that started this effort) so packaging regressions surface.
- The B shim should guard `build_wheel` only and NOT enforce on `build_editable`
  — a dev may install editable before building assets, and we shouldn't block
  that. Result: enforcement on release wheels, freedom in dev.

## Dev workflow (focus)

Dev uses an **editable** install of openedx-platform, so the "installed" package
*is* the live checkout — which already has `package.json`, webpack configs,
`scripts/`, JS/Sass sources, and (after `npm ci`) `node_modules`. The
wheel-only "ship the root build tooling" wrinkle therefore does NOT apply in dev.

With `DEBUG=True`, Django's `staticfiles` finders serve static **live** from the
source tree — **no `collectstatic` in dev**. So we only need the build artifacts
written into the checkout's `static/` dirs, where `build-dev`/`watch` already
write them.

Invoking the build (two equivalent options):
- (a) **Console script** (recommended, location-agnostic; identical command in
  dev → editable checkout and prod → site-packages):
  `build_legacy_openedx_platform_frontends --dev`
- (b) **Just run npm in the checkout**: `npm ci && npm run build-dev`
  (or `npm run watch` for the live-rebuild loop).

```bash
# openedx-site
pip install -e ../openedx-platform
build_legacy_openedx_platform_frontends --dev          # or: (cd ../openedx-platform && npm run build-dev)
DJANGO_SETTINGS_MODULE=... ./manage.py lms runserver    # serves live, no collectstatic
```

Do NOT auto-run npm during `pip install` (rejected "option C" magic) — keep the
asset build explicit.

### Where node_modules lives (decided: in the platform checkout)

We considered relocating `node_modules` to openedx-site (mirroring how `.venv`
lives in openedx-site). **Decision: keep `node_modules` in the openedx-platform
checkout** (`npm ci` there, as the platform already expects; it's gitignored).
openedx-site stays Python-only.

Why not relocate it to site (the JS "editable install" idea):

- **Node resolves `node_modules` by walking UP from each source file.**
  openedx-platform is a *sibling* of openedx-site, and its webpack is hard-wired
  to its own root (`resolve.modules: [__dirname, 'node_modules']`, outputs to
  `__dirname/common/static/bundles`). Platform files can never see
  `openedx-site/node_modules` without symlink trickery or rewriting resolve.
- **devDependencies aren't installed transitively.** The build toolchain
  (webpack + 24 devDeps) is in the platform's `devDependencies`. A
  `file:`-linked dependency installs a package's `dependencies` but NOT its
  `devDependencies`, so a site-owned `node_modules` wouldn't get webpack itself.
- An npm **workspace at the common parent `openedx/`** would solve both cleanly
  (hoisted tree that's an ancestor of platform files; installs devDeps; no
  webpack changes — only a small `copy-node-modules.sh` path tweak). Kept as a
  future option, but not worth it for a sunsetting legacy build.

Net: given the legacy frontend build is being deleted within ~a year, investing
in relocating its node_modules isn't worth the fragility. `npm ci` in the
platform checkout it is.

## Source dir sizes

| dir | size | tracked files |
|---|---|---|
| common/static | 109M | 1050 |
| openedx | 27M | 2099 |
| xmodule/js | 20M | 135 |
| lms/static | 15M | 774 |
| cms/static | 6.8M | 334 |
