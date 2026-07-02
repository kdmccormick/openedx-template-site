"""
Enable the waffle flags/switches that stable MFEs and features depend on, so
this platform behaves like production (redirecting to MFE versions of pages
wherever a stable MFE exists). This mirrors what Tutor turns on in its init
scripts; "enabled in Tutor" is our signal that an MFE/feature is stable.

Only the toggles that (a) still exist upstream and (b) are default-off are set
here. Tutor also toggles ~25 others that are now deleted upstream because their
feature became the default (new Studio pages, new editors, courseware sidebars);
setting those would only create orphan waffle rows. See
docs/waffle-flags-tutor-vs-upstream.md for the full cross-reference.

Idempotent (get_or_create won't clobber an explicitly-set value); reverse is a
no-op so a rollback doesn't drop flags that may have pre-existed.
"""
from django.db import migrations


def enable_toggles(apps, schema_editor):
    # Import the toggle definitions for their `.name` (the DB row name). Deferred
    # to call time so loading the migration graph never imports these app
    # modules (they import fine under both LMS and CMS, but this keeps it cheap).
    # The resolved db-name string is noted next to each import.
    from completion.waffle import ENABLE_COMPLETION_TRACKING_SWITCH  # completion.enable_completion_tracking
    from lms.djangoapps.course_home_api.toggles import COURSE_HOME_MICROFRONTEND_PROGRESS_TAB  # course_home.course_home_mfe_progress_tab
    from lms.djangoapps.discussion.toggles import ENABLE_DISCUSSIONS_MFE  # discussions.enable_discussions_mfe
    from lms.djangoapps.learner_home.waffle import ENABLE_LEARNER_HOME_MFE  # learner_home_mfe.enabled
    from openedx.core.djangoapps.discussions.config.waffle import (
        ENABLE_NEW_STRUCTURE_DISCUSSIONS,           # discussions.enable_new_structure_discussions
        ENABLE_PAGES_AND_RESOURCES_MICROFRONTEND,   # discussions.pages_and_resources_mfe
    )

    Flag = apps.get_model("waffle", "Flag")
    Switch = apps.get_model("waffle", "Switch")

    flag_names = [
        ENABLE_LEARNER_HOME_MFE.name,
        COURSE_HOME_MICROFRONTEND_PROGRESS_TAB.name,
        ENABLE_PAGES_AND_RESOURCES_MICROFRONTEND.name,
        ENABLE_NEW_STRUCTURE_DISCUSSIONS.name,
        ENABLE_DISCUSSIONS_MFE.name,
        # No clean module-level constant: this CourseWaffleFlag is built inline
        # in lms/djangoapps/ora_staff_grader/views.py from edx-ora2 constants.
        "openresponseassessment.enhanced_staff_grader",
    ]
    for name in flag_names:
        Flag.objects.get_or_create(name=name, defaults={"everyone": True})

    Switch.objects.get_or_create(
        name=ENABLE_COMPLETION_TRACKING_SWITCH.name,  # completion.enable_completion_tracking
        defaults={"active": True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("waffle", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(enable_toggles, reverse_code=migrations.RunPython.noop),
    ]
