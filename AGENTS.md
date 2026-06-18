## Guidance for all agents

* Read this file and README.md.
* Update this file with new instructions.
* Ask questions eagerly.
* read `../openedx-platform` *only as needed*. It's a huge codebase; don't burn tokens delving unneccessarily.
* Commit often.
* Don't test things out unless asked.
* When asked to test things out, use the virtualenv at `.venv`.

## Overview

This is a new repo which is intended to run Open edX in a simpler, Tutor-free way. We want to adhere to a standard Django pattern: that is, this is repo is a *Django project* which installs openedx-platform (currently locally installed at at ../openedx-platform) as a set of *reusable apps*.

openedx-platform is not typically run this way, so there will be some challenges, and we'll need to make some changes upstream in openedx-platform. The current known challenges are:

* static assets. openedx-platform builds static assets with `npm run build`, but it does not bundle them into the installable package, so they are missing when running in the openedx-site context. I think this is why `./manage.py migrate` is currently failing.
