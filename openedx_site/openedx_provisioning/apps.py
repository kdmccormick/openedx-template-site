"""
App config for openedx_provisioning.

This app carries no models. It exists to host data migrations that provision
Open edX database state (waffle flags/switches, and later other seed data) that
would otherwise have to live in a downstream-only provision.sh. Because it is
installed in both the LMS and CMS (which share one database), each migration
runs once, tracked in django_migrations. See docs/provisioning-via-migrations.md.

The "openedx_" prefix marks the app as Open edX-specific even when read outside
the openedx_site context.
"""
from django.apps import AppConfig


class OpenedxProvisioningConfig(AppConfig):
    name = "openedx_site.openedx_provisioning"
    label = "openedx_provisioning"
    verbose_name = "Open edX Provisioning"
