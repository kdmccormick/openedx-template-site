#!/bin/bash

./manage.py shell -c '
from django.contrib.auth import get_user_model
User = get_user_model()
user, _ = User.objects.get_or_create(
    username="openedx",
    defaults={"email": "openedx@local.openedx.io"},
)
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.set_password("openedx")
user.save()
'
