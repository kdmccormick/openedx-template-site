#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

@@TODO this does not fully work yet. For now, just use
openedx-platform's manage.py
"""
import os
import sys
from path import Path


def main():
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
