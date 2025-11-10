from __future__ import annotations

import json
import logging
from collections import defaultdict
from collections.abc import Iterable, Iterator

import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import CKANConfig
from ckan.plugins import PluginImplementations

from ckanext.syndicate import config
from ckanext.syndicate.interfaces import ISyndicate
from ckanext.syndicate.types import Profile, Topic

PROFILE_PREFIX = "ckanext.syndicate.profile."
log = logging.getLogger(__name__)


def syndicate_dataset(package_id: str, topic: Topic, profile: Profile):
    """Enqueue syndication job.

    If you need realtime syndication, use `syndicate_sync` action.
    """
    tk.enqueue_job(sync_package, [package_id, topic, profile], queue=config.get_queue_name())


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


def get_profiles() -> Iterator[Profile]:
    yield from _parse_profiles(tk.config)


def _parse_profiles(config: CKANConfig) -> Iterable[Profile]:
    profiles = defaultdict(dict)
    for opt, v in config.items():
        if not opt.startswith(PROFILE_PREFIX):
            continue
        profile, attr = opt[len(PROFILE_PREFIX) :].split(".", 1)
        profiles[profile][attr] = v

    for id_, data in profiles.items():
        try:
            data["extras"] = json.loads(data.get("extras", "{}"))
        except (TypeError, ValueError):
            data["extras"] = {}

        yield Profile(id=id_, **data)


def get_profile(profile_id: str) -> Profile | None:
    for profile in get_profiles():
        if profile.id != profile_id:
            continue

        return profile


def profiles_for(pkg: model.Package):
    implementations = PluginImplementations(ISyndicate)
    skipper: ISyndicate = next(iter(implementations))

    for profile in get_profiles():
        if skipper.skip_syndication(pkg, profile):
            log.debug(
                "Plugin %s decided to skip syndication of %s for profile %s",
                skipper.name,
                pkg.id,
                profile.id,
            )
            continue
        yield profile
