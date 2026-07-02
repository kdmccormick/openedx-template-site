# Waffle flags/switches: Tutor overrides vs. openedx-platform

Cross-reference of every waffle toggle that **tutor** and **tutor-mfe** set in
their init scripts against the definitions in **openedx-platform**, to decide
which are worth setting in our own data migrations.

## Method

- Overrides gathered from `tutor .../jobs/init/lms.sh` (1 switch) and
  `tutor-mfe .../mfe/tasks/lms/init` (the flags). "Override true" =
  `waffle_flag --create --everyone` / `waffle_switch ... on`; "override false"
  = `--create --deactivate`.
- A definition in openedx-platform has the form
  `PYTHON_NAME = <ToggleType>(<db_name>, ...)`, where `<db_name>` is often built
  from a namespace constant (e.g. `f"{WAFFLE_FLAG_NAMESPACE}.enable_discussions_mfe"`).
- **default true** iff a data migration sets the flag `everyone=True` (switch
  `active=True`); openedx-platform's toggle wrappers forbid a default-true on
  the definition itself, so a migration is the only mechanism. **default false**
  = defined but no such migration. **deleted** = no definition found in this
  openedx-platform checkout.

Caveats: this reflects one openedx-platform checkout (re-run on upgrade). A few
toggles are defined in **dependency packages** (`edx-completion`, `edx-ora2`),
not the platform repo — noted in footnotes.

## Table

| flag/switch name | type | tutor status | openedx-platform status | openedx-platform Python name |
|---|---|---|---|---|
| `completion.enable_completion_tracking` | WaffleSwitch | override true | default false ¹ | `ENABLE_COMPLETION_TRACKING_SWITCH` ¹ |
| `learner_home_mfe.enabled` | WaffleFlag | override true | default false | `ENABLE_LEARNER_HOME_MFE` |
| `course_home.course_home_mfe_progress_tab` | CourseWaffleFlag | override true | default false | `COURSE_HOME_MICROFRONTEND_PROGRESS_TAB` |
| `discussions.pages_and_resources_mfe` | CourseWaffleFlag | override true | default false | `ENABLE_PAGES_AND_RESOURCES_MICROFRONTEND` |
| `discussions.enable_discussions_mfe` | CourseWaffleFlag | override true | default false | `ENABLE_DISCUSSIONS_MFE` |
| `discussions.enable_new_structure_discussions` | CourseWaffleFlag | override true | default false | `ENABLE_NEW_STRUCTURE_DISCUSSIONS` |
| `openresponseassessment.enhanced_staff_grader` | CourseWaffleFlag | override true | default false | `enhanced_staff_grader_flag` ² |
| `courseware.enable_navigation_sidebar` | Unknown | override true | deleted ³ | None |
| `courseware.always_open_auxiliary_sidebar` | Unknown | override **false** | deleted ³ | None |
| `contentstore.new_studio_mfe.use_new_advanced_settings_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_certificates_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_course_outline_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_course_team_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_custom_pages` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_export_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_files_uploads_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_grading_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_group_configurations_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_import_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_schedule_details_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_textbooks_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_unit_page` | Unknown | override true | deleted ⁴ | None |
| `contentstore.new_studio_mfe.use_new_updates_page` | Unknown | override true | deleted ⁴ | None |
| `new_studio_mfe.use_new_home_page` | Unknown | override true | deleted ⁴ | None |
| `new_studio_mfe.use_tagging_taxonomy_list_page` | Unknown | override true | deleted ⁴ | None |
| `new_core_editors.use_new_problem_editor` | Unknown | override true | deleted ⁵ | None |
| `new_core_editors.use_new_text_editor` | Unknown | override true | deleted ⁵ | None |
| `new_core_editors.use_new_video_editor` | Unknown | override true | deleted ⁵ | None |
| `discussions.enable_learners_tab_in_discussions_mfe` | Unknown | override true | deleted ⁶ | None |
| `discussions.enable_moderation_reason_codes` | Unknown | override true | deleted ⁶ | None |
| `discussions.enable_reported_content_email_notifications` | Unknown | override true | deleted ⁶ | None |
| `discussions.enable_learners_stats` | Unknown | override true | deleted ⁶ | None |

**Footnotes**
1. Defined in the `edx-completion` dependency (`completion/waffle.py`), not the
   openedx-platform repo. No migration activates it → default false.
2. Instantiated inline in `lms/djangoapps/ora_staff_grader/views.py` as
   `CourseWaffleFlag(f"{WAFFLE_NAMESPACE}.{ENHANCED_STAFF_GRADER}", ...)`; the
   name constants come from the `edx-ora2` (`openassessment`) dependency. No
   openedx-platform migration sets it → default false.
3. The courseware navigation/auxiliary sidebars are now standard; the flags were
   removed.
4. The new Studio pages are now the default. These `use_new_*` flags were
   deleted and replaced by inverse **opt-out** flags in
   `contentstore/toggles.py` (e.g. `use_new_unit_page()` now returns
   `not LEGACY_STUDIO_UNIT_EDITOR.is_enabled()`, flag `legacy_studio.unit_editor`).
   Net effect: the new pages are on by default with no flag needed.
5. The new problem/text/video editors are now the default (see
   `legacy_studio.*` opt-out flags). `new_core_editors` now only defines
   `use_video_gallery_flow`.
6. No definition found in openedx-platform — these appear to be
   discussions-MFE-side (frontend) flags, not backend waffle toggles.

## Summary / implication for our migration

- **7 survive as real, default-false toggles** → the meaningful set to set
  `everyone=True` (switch `active=True`) in `openedx_site.openedx_provisioning`:
  `completion.enable_completion_tracking` (switch),
  `learner_home_mfe.enabled`, `course_home.course_home_mfe_progress_tab`,
  `discussions.pages_and_resources_mfe`, `discussions.enable_discussions_mfe`,
  `discussions.enable_new_structure_discussions`,
  `openresponseassessment.enhanced_staff_grader`.
- **0 are set by an upstream migration** — no overlap to defer to upstream.
- **25 are deleted/absent** — mostly because their feature became the upstream
  default (new Studio pages, new editors, courseware sidebars). Setting these
  would only create orphan waffle rows; **skip them**.

So of Tutor's 31 flags + 1 switch, we only need ~7 toggles to reach feature
parity; the rest are obsolete in this platform version.
