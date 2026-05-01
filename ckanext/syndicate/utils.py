from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Iterator
from functools import lru_cache

import ckan.plugins.toolkit as tk
from ckan import model
from ckan.plugins import PluginImplementations

from ckanext.syndicate.interfaces import ISyndicate
from ckanext.syndicate.model import SyndicationLog
from ckanext.syndicate.types import Profile, Topic

PROFILE_PREFIX = "ckanext.syndicate.profile."
log = logging.getLogger(__name__)


def syndicate_dataset(package_id: str, topic: Topic, profile: Profile):
    """Enqueue syndication job.

    If you need realtime syndication, use `syndicate_sync` action.
    """
    tk.enqueue_job(sync_package, [package_id, topic, profile], queue=profile.queue)


def sync_all_profiles(foreground: bool = False) -> None:
    packages = model.Session.query(model.Package)
    profiles = list(get_profiles())

    log.info("Syncing %s packages to %s profiles", packages.count(), len(profiles))

    for package in packages:
        for profile in profiles_for(package):
            if foreground:
                sync_package(package.id, Topic.update, profile)
            else:
                syndicate_dataset(package.id, Topic.update, profile)


def sync_profile(profile_id: str, foreground: bool = False) -> None:
    profile = get_profile(profile_id)

    if not profile:
        log.error("Profile %s not found", profile_id)
        return

    packages = model.Session.query(model.Package)

    log.info("Syncing %s packages to profile %s", packages.count(), profile.id)

    for package in packages:
        if profile not in profiles_for(package):
            continue

        if foreground:
            sync_package(package.id, Topic.update, profile)
        else:
            syndicate_dataset(package.id, Topic.update, profile)


def sync_package(package_id: str, action: Topic, profile: Profile) -> None:
    log.info(
        "Sync package %s, with action %s to the %s",
        package_id,
        action.name,
        profile.id,
    )

    tk.get_action("syndicate_sync")(
        {"ignore_auth": True},
        {"id": package_id, "topic": action.name, "profile": profile.id},
    )


def get_profiles(force_refresh: bool = False) -> list[Profile]:
    """Yield all configured syndication profiles."""
    if force_refresh:
        _get_profiles_cached.cache_clear()
    return _get_profiles_cached()


@lru_cache(maxsize=1)
def _get_profiles_cached() -> list[Profile]:
    profiles = defaultdict(dict)

    for opt, v in tk.config.items():
        if not opt.startswith(PROFILE_PREFIX):
            continue

        profile, attr = opt[len(PROFILE_PREFIX) :].split(".", 1)
        profiles[profile][attr] = v

    return [Profile(id=id_, **data) for id_, data in profiles.items()]


def get_profile(profile_id: str) -> Profile | None:
    """Get a syndication profile by its ID."""
    for profile in get_profiles():
        if profile.id != profile_id:
            continue

        return profile


def profiles_for(pkg: model.Package) -> Iterator[Profile]:
    """Yield profiles applicable for the given package."""
    skipper: ISyndicate = next(iter(PluginImplementations(ISyndicate)))

    for profile in get_profiles():
        if reason := skipper.skip_syndication(pkg, profile):
            log.debug(
                "Plugin %s decided to skip syndication of %s for profile %s: %s",
                skipper.name,
                pkg.id,
                profile.id,
                reason,
            )
            SyndicationLog.write(
                local_id=pkg.id,
                profile_id=profile.id,
                state=SyndicationLog.State.STOPPED,
            )
            continue
        yield profile
