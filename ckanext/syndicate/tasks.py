from __future__ import annotations

import logging

import ckan.plugins.toolkit as tk

from .types import Profile, Topic

log = logging.getLogger(__name__)


def sync_package(package_id: str, action: Topic, profile: Profile):
    log.info(
        "Sync package %s, with action %s to the %s",
        package_id,
        action.name,
        profile.id,
    )
    user = tk.get_action("get_site_user")({"ignore_auth": True}, {})
    tk.get_action("syndicate_sync")(
        {"user": user["name"]},
        {"id": package_id, "topic": action.name, "profile": profile.id},
    )
