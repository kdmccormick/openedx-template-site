# Code style

Kyle's taste as a software engineer, accumulated from PR review so it compounds
instead of getting relitigated every PR.

Entries go in only when Kyle has actually said something, in review or in chat —
this is a record of real feedback, not a guess at what he'd probably want. Cite
the PR so the original wording stays findable. If two entries ever conflict, the
newer one wins and the older one gets deleted rather than left to rot.

Rules that live elsewhere aren't repeated here (same single-source-of-truth
reasoning as `AGENTS.md`'s "add defaults in exactly one place"): see `AGENTS.md`
for feature-toggle style, config defaults, and workflow.

## Comments: 80/20 the understanding

Optimize a comment for how fast a reader groks it, not for how completely it
pins down the truth. Give up a little precision to get there. If a detail is
re-derivable by reading the file next to it, cut it.

> "Try to be more concise. De-prioritize precision just a bit for readability."
> "Just chill it out a bit, focus on easy-to-grok. '80/20' the understanding, if you will."
> — [#1](https://github.com/kdmccormick/openedx-template-site/pull/1)

Before (10 lines, and the reader is now an expert on mysql image internals):

```
# MySQL. Three consumers read these names:
#  1. the official mysql image's entrypoint, which creates MYSQL_DATABASE and
#     MYSQL_USER/MYSQL_PASSWORD -- but only while the datadir is empty, so once
#     per volume, not per container (compose.yml passes this file as env_file);
#  2. provision.sh, which reconciles the same objects on every run, covering
#     changes made here after the volume was already initialised;
#  3. our Django settings overrides (shared_settings_overrides_dev.py), which
#     build DATABASES from them.
# MYSQL_ROOT_* is ours alone (provision.sh, sqlshell.sh); the image's own name
# for the password is MYSQL_ROOT_PASSWORD, which is why it's spelled that way.
```

After (6 lines, same working understanding):

```
# MySQL. Three consumers:
#  1. compose.yml passes these to the official mysql image's entrypoint, which
#     initializes the db and user when the data volume is empty.
#  2. provision.sh, which re-applies them on every run.
#  3. our dev settings overrides, which build DATABASES.
# MYSQL_ROOT_* is just for our own scripts (provision.sh, sqlshell.sh).
```

Failure modes this is correcting, both of them mine:

* **Narrating detail nobody asked about.** Explaining *why* `MYSQL_ROOT_PASSWORD`
  is spelled that way answers a question no reader was going to ask.
* **Hedging into precision.** "reconciles the same objects on every run, covering
  changes made here after the volume was already initialised" is more exactly
  true than "re-applies them on every run" and communicates less.

**The exception**: keep the sentence that stops someone from reintroducing a bug.
A comment earns its length when it documents a silent failure or a trap that the
obvious refactor walks straight into — those aren't re-derivable from the code,
because the code is exactly what looks fine.
