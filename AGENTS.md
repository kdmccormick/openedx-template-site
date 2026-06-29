# Working on openedx-template-site

This file is for **core-team engineers** (Kyle and other Open edX maintainers)
working on the openedx-template-site infrastructure itself. We treat the repo as
a work-in-progress *project*.

> **Helping someone *operate* a site instead?** If you're helping a site operator
> or community developer with day-to-day admin tasks (settings, URLs, plugins,
> services) rather than building the template, you're **Open edX Site Buddy** —
> invoke the `/site-buddy` skill (see `.claude/skills/site-buddy/`), which treats
> the repo as a *product* rather than a WIP project.

* Read this file and README.md. Keep this file updated with new instructions.
* Ask questions eagerly, and check in before deep-diving into the large upstream repos below.
* External references (read-only, don't overfit to them):
  * `../openedx-platform` and `../frontend-app-*` — upstream sources. Huge; they'll fill your context window, so don't delve deep unless necessary.
  * `../../overhangio/tutor` and `../../overhangio/tutor-*` — Tutor and its plugins configure/run Open edX. Treat as extended documentation; we're building something smaller and simpler, so don't copy Tutor patterns.
* Use `rg`, not `grep`.
* Don't test things out unless asked. When asked, first source `env` (loads `env_vars` and activates `.venv`).
* When you learn something significant that doesn't fit in a code comment, write it up in `docs/`.
* Commit often.

## Overview

This is a new repo for running Open edX in a simpler, Tutor-free way, following a standard Django pattern: this repo is a *Django project* that installs openedx-platform (currently from `../openedx-platform`) as a set of *reusable apps*.

openedx-platform isn't typically run this way, so expect challenges and some required upstream changes. Known challenges:

* **Static assets.** openedx-platform builds assets with `npm run build` but doesn't bundle them into the installable package, so they're missing in the openedx-site context. See `docs/static-assets-discovery.md`.

The above challenge(s) are blocking enough that we are currently opting to just run openedx-platform directly (see manage.py). We're also only targeting dev now. These are both temporary.
