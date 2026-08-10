# ProblemBlock Static Asset Build Pipeline

This doc covers how static assets (JS/CSS) are built and served for the new `ProblemBlock`
in [xblocks-core](https://github.com/openedx/xblocks-core), and the current state of its
extraction from openedx-platform.

## Status: Two Parallel Builds — No Conflict

openedx-platform's `webpack.builtinblocks.config.js` still has a `ProblemBlockDisplay` entry
sourcing `xmodule/js/src/capa/display.js` etc., so **two separate `ProblemBlockDisplay.js`
bundles are built**. They do not conflict because they land in completely different places and
are referenced by different code paths.

When `USE_EXTRACTED_PROBLEM_BLOCK=True` (the hardcoded value in `common.py`, though the toggle
annotation still says `toggle_default: False` with a "Not production-ready" warning — the
annotation appears stale; see [edx-platform#34827](https://github.com/openedx/edx-platform/issues/34827)):

- The active class is `_ExtractedProblemBlock` (imported from `xblocks_contrib.problem.capa_block`)
- Its `student_view` uses `local_resource_url` → xblocks-core bundle (see table below)
- The platform bundle (`common/static/bundles/ProblemBlockDisplay.js`) is collected but **never referenced** — dead weight

When `USE_EXTRACTED_PROBLEM_BLOCK=False`:

- The active class is `_BuiltInProblemBlock` (defined in `xmodule/capa_block.py`)
- Its `student_view` calls `add_webpack_js_to_fragment("ProblemBlockDisplay")` → platform bundle via `webpack_loader`/`webpack-stats.json`
- The xblocks-core bundle is irrelevant

| | Source | Output | URL |
|---|---|---|---|
| **Extracted** (active when flag=True) | `xblocks_contrib/problem/assets/static/js/` | `xblocks_contrib/problem/public/js/ProblemBlockDisplay.js` | `xblock/resources/xblocks_contrib.problem/problem/public/js/ProblemBlockDisplay.js` |
| **Built-in** (active when flag=False) | `xmodule/js/src/capa/` | `common/static/bundles/ProblemBlockDisplay.js` | `bundles/ProblemBlockDisplay.js` (via webpack-stats.json) |

The platform's `ProblemBlockDisplay` webpack entry is wasteful but harmless — it can be
removed once `_BuiltInProblemBlock` is fully retired.

## xblocks-core Build

### Source files

```
xblocks_contrib/problem/assets/static/js/
  xmodule.js
  javascript_loader.js
  display.js
  collapsible.js
  imageinput.js
  schematic.js
  vendor/codemirror-compressed.js

xblocks_contrib/problem/assets/static/css/
  ProblemBlockDisplay.css
```

### Build command

From the repo root:

```sh
npm run build          # production (minified)
npm run build-dev      # development (source maps, unminified)
npm run watch-build-dev  # watch mode
```

These delegate to each workspace. For ProblemBlock specifically, it runs:

```sh
cd xblocks_contrib/problem/assets
webpack --config=webpack.prod.config.js
```

The webpack config (`assets/webpack.config.js`) strips RequireJS AMD boilerplate
(`define`/`require` wrappers) from the source files via `string-replace-loader`, since those
files were originally written for RequireJS.

### Build output

```
xblocks_contrib/problem/public/js/ProblemBlockDisplay.js
xblocks_contrib/problem/public/css/ProblemBlockDisplay.css
```

The `public/` directory is what gets shipped in the Python wheel. `MANIFEST.in` includes it
(`recursive-include xblocks_contrib *.js *.css`) and explicitly prunes the raw source via
`prune xblocks_contrib/*/assets`.

## How Django Serves the Assets

### Production (`PIPELINE_ENABLED=True`)

openedx-platform registers `XBlockPipelineFinder` as a Django `STATICFILES_FINDER`. On startup
it creates an `XBlockPackageStorage` for each installed XBlock, rooted at the XBlock's parent
Python package. For `ProblemBlock` (module `xblocks_contrib.problem.capa_block`):

- Package name: `xblocks_contrib.problem`
- Static prefix: `xblock/resources/xblocks_contrib.problem/`
- Files on disk: rooted at the `xblocks_contrib/` package directory

`collectstatic` picks up `xblocks_contrib/problem/public/js/ProblemBlockDisplay.js` and
publishes it as:

```
xblock/resources/xblocks_contrib.problem/problem/public/js/ProblemBlockDisplay.js
```

### Development (`PIPELINE_ENABLED=False`)

Requests go to the `xblock_resource` Django view, which calls
`ProblemBlock.open_local_resource(uri)`. This uses `importlib.resources` to serve directly
from the installed package's `public/` directory (`xblocks_contrib/problem/public/`).

### How the block wires it up

`capa_block.py` `student_view()` adapts the path based on the environment:

```python
use_pipeline = pipeline.get("PIPELINE_ENABLED", True) or not getattr(settings, "REQUIRE_DEBUG", False)
base_path = "problem/public" if use_pipeline else "public"

fragment.add_css_url(self.runtime.local_resource_url(self, f"{base_path}/css/ProblemBlockDisplay.css"))
fragment.add_javascript_url(self.runtime.local_resource_url(self, f"{base_path}/js/ProblemBlockDisplay.js"))
```

The extra `problem/` prefix in production is what routes through the `xblocks_contrib` package
root correctly — without it, the static file finder can't locate the file on disk.

## Full Pipeline Diagram

```
assets/static/js/*.js  +  assets/static/css/ProblemBlockDisplay.css
        │
        ▼  npm run build  (webpack --config=webpack.prod.config.js)
        │  strips RequireJS AMD wrappers, bundles, minifies
        │
xblocks_contrib/problem/public/js/ProblemBlockDisplay.js
xblocks_contrib/problem/public/css/ProblemBlockDisplay.css
        │
        ▼  pip wheel / install  (MANIFEST.in ships public/, excludes assets/)
        │
installed Python package
        │
        ├─ Production: collectstatic via XBlockPipelineFinder → CDN
        │   URL: /static/xblock/resources/xblocks_contrib.problem/problem/public/js/ProblemBlockDisplay.js
        │
        └─ Dev: xblock_resource view → open_local_resource()
            URL: /xblock/resource/problem/public/js/ProblemBlockDisplay.js
```

## What Still Needs to Be Done

To complete the extraction, openedx-platform needs to:

1. Remove `_BuiltInProblemBlock` and the `reset_class()` flag-switching shim from `xmodule/capa_block.py`
2. Remove the `ProblemBlockDisplay` entry from `webpack.builtinblocks.config.js`
3. Delete `xmodule/js/src/capa/display.js`, `imageinput.js`, `schematic.js` (and related
   capa JS sources that have been moved to xblocks-core)
4. Delete `xmodule/static/css-builtin-blocks/ProblemBlockDisplay.css`
