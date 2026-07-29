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
* In settings overrides, read/write feature toggles as **top-level settings** (`ENABLE_FOO = True`), never `FEATURES["ENABLE_FOO"]` — the latter is deprecated and support will be removed. The two are kept equivalent/live-synced by `FEATURES = FeaturesProxy(globals())` near the top of each root settings module; don't remove that line.
* Don't test things out unless asked. When asked, source `env` (loads `env_vars` and activates `.venv`). Each shell invocation is fresh and shell state does NOT persist between commands, so prefix every `./manage.py` (or other env-dependent) call with it in the *same* command, e.g. `source env && ./manage.py ...`. Without it, `DJANGO_SETTINGS_MODULE` is unset and manage.py errors with "could not determine system for settings".
  * For CMS/Studio management commands, source `env_cms` instead of `env` (same as `env` except it switches `DJANGO_SETTINGS_MODULE` to `openedx_site.settings_cms_dev`). LMS is the default.
* Add defaults in exactly *one* place. For example, if shell environment var has default defined in env\_vars and you're loading it into a django setting within one of the openedx\_site/settings files, then don't redundantly do `os.environ.get('ENV_VAR_NAME', spurious_default)`. The ENV\_VAR is always present and spurious\_default is never used and thus subject to drift. Just do `os.environ['ENV_VAR_NAME']`. Follow a similar philosophy for other configuration points, too.
* When you learn something significant that doesn't fit in a code comment, write it up in `docs/`.
* Read `docs/code-style.md` before writing code. It's Kyle's taste as a software engineer,
  accumulated from PR review, and it grows every time he gives feedback.
* Commit often.

## Overview

This is a new repo for running Open edX in a simpler, Tutor-free way, following a standard Django pattern: this repo is a *Django project* that installs openedx-platform (currently from `../openedx-platform`) as a set of *reusable apps*.

openedx-platform isn't typically run this way, so expect challenges and some required upstream changes. Known challenges:

* **Static assets.** openedx-platform builds assets with `npm run build` but doesn't bundle them into the installable package, so they're missing in the openedx-site context. See `docs/static-assets-discovery.md`.

The above challenge(s) are blocking enough that we are currently opting to just run openedx-platform directly (see manage.py). We're also only targeting dev now. These are both temporary.

## Git and GitHub workflow

The goal is for LLM agents to iterate fast without permission prompts, while making
it structurally impossible for a haywire agent to spam Kyle's or anyone else's
upstream repos. Push freely to your own fork; reach Kyle's fork only via pull request.

**Remotes.** Two, and they are not interchangeable:

* `origin` → `kdmccormick/openedx-template-site` — Kyle's fork. **Fetch-only.** Its push URL is
  deliberately set to the bogus value `DISABLED_READ_ONLY_UPSTREAM` so `git push origin` fails
  immediately instead of hitting the network. Belt and braces: the GitHub account these
  credentials belong to (`kylemakor-ai`) has no write access to it anyway.
* `aifork` → `kylemakor-ai/openedx-template-site` — the AI account's fork. **Yours.** Push
  anything, branch however you like, force-push branches nobody is reviewing yet.

`remote.pushDefault` is `aifork`, so a bare `git push` goes to your fork while `git fetch`
and branch tracking still follow `origin`. To undo any of this local config:
`git config --local --unset remote.pushDefault` and `git remote set-url --delete --push origin DISABLED_READ_ONLY_UPSTREAM`.

**Branches and commits.**

* Local `main` is a read-only mirror of `origin/main`. **Never commit to it.** Sync with
  `git fetch origin && git checkout main && git reset --hard origin/main`.
* Work on `ai/<topic>` branches cut from `main`. Commit often, push to `aifork` often — that
  costs nothing and needs no approval.
* Repo-local git identity is `Kyle D McCormick's AI <ai@kylemccormick.me>`, so AI commits are
  visibly not Kyle's. Kyle's own commits may intermingle on the same branch, exactly as two
  coworkers' would; never rewrite the authorship of a commit you didn't write.

**Opening a PR.** From `aifork` toward `origin`, always naming the base repo explicitly:

```
gh pr create --repo kdmccormick/openedx-template-site \
  --base main --head kylemakor-ai:ai/<topic> --title "..." --body "..."
```

⚠️ **Always pass `--repo`.** Both forks descend from `feanil/minimal-edx-platform`, and GitHub
defaults a fork's PR base to the *network root* — so a bare `gh pr create` would open a pull
request against **feanil's** repo. `gh repo set-default kdmccormick/openedx-template-site` is
configured to prevent that, but don't rely on it; be explicit every time.

**Scope of GitHub access.** You have the `kylemakor-ai` account's full access, restricted by this
rule rather than by permissions: **interact with, and open PRs on, repos owned by `kdmccormick`
or `kylemakor-ai`, and nothing else.** No PRs, issues, comments, reactions, or stars on any other
owner's repos — not `feanil/*`, not `openedx/*`, not the upstreams of `../openedx-platform` or
`../frontend-app-*`. Also: don't edit remotes, don't touch repo settings, workflows, or secrets,
and don't delete anything on GitHub.

The credentials are broadly scoped (`repo`, `admin:org`, `delete_repo`, `workflow`, `gist`) and
nothing technical stops you from breaking that rule, so it's on you to hold the line. If you
think you need to reach outside that scope, ask Kyle rather than doing it. Kyle merges; you
have no write access to `origin`, so never try.

**Responding to review.** Currently triggered by Kyle saying "pls respond to PR review"; someday
this should fire automatically.

* Read the conversation: `gh pr view <N> --repo kdmccormick/openedx-template-site --comments`
* Read inline comments *with the IDs needed to reply*:
  `gh api repos/kdmccormick/openedx-template-site/pulls/<N>/comments --jq '.[] | {id, path, line, user: .user.login, body}'`
* Reply in-thread:
  `gh api --method POST repos/kdmccormick/openedx-template-site/pulls/<N>/comments/<COMMENT_ID>/replies -f body='...'`
* Reply at top level: `gh pr comment <N> --repo kdmccormick/openedx-template-site --body '...'`
* Answer **every** comment, including ones you disagree with — say so and why, rather than
  silently complying or silently ignoring.
* Address feedback with **new commits pushed on top**, not a force-push: review threads stay
  anchored to their lines and Kyle can see just what changed since he looked. Squash at merge.
* Don't resolve review threads yourself. The reviewer decides when a comment is settled.
* Say your piece on GitHub, not twice. Kyle reads the PR, so report back in chat with just
  "Responded to review on \<links\>" / "Nothing to respond to" / "Blocked by questions on
  \<links\>". Don't re-summarize what the comments already say.
* When feedback is about *taste* rather than this one diff — naming, comment density, structure,
  how much abstraction is too much — add it to `docs/code-style.md` so it compounds instead of
  being relitigated every PR. Apply it to the whole diff, not only the lines Kyle flagged; he's
  pointing at an instance of a pattern, not filing one-off nitpicks.
