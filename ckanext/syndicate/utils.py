# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import warnings
from collections import defaultdict
from itertools import zip_longest
from typing import Iterable, Iterator, Optional

import ckanapi

import ckan.model as ckan_model
import ckan.plugins.toolkit as tk
from ckan.lib.jobs import DEFAULT_QUEUE_NAME
from ckan.plugins import PluginImplementations, get_plugin

from .interfaces import ISyndicate
from .types import Profile, Topic

try:
    from ckan.exceptions import CkanDeprecationWarning
except ImportError:
    CkanDeprecationWarning = DeprecationWarning


class SyndicationDeprecationWarning(CkanDeprecationWarning):  # type: ignore
    pass


CONFIG_QUEUE_NAME = "ckanext.syndicate.queue.name"
PROFILE_PREFIX = "ckanext.syndicate.profile."
log = logging.getLogger(__name__)


def deprecated(msg: str):
    log.warning(msg)
    warnings.warn(msg, category=SyndicationDeprecationWarning, stacklevel=3)


def syndicate_dataset(package_id: str, topic: Topic, profile: Profile):
    """Enqueue syndication job.

    If you need realtime syndication, use `syndicate_sync` action.
    """
    import ckanext.syndicate.tasks as tasks

    tk.enqueue_job(
        tasks.sync_package,
        [package_id, topic, profile],
        queue=tk.config.get(CONFIG_QUEUE_NAME, DEFAULT_QUEUE_NAME),
    )


def prepare_profile_dict(profile: Profile) -> Profile:
    return profile


def syndicate_configs_from_config(config) -> Iterable[Profile]:
    prefix = "ckan.syndicate."
    keys = (
        "api_key",
        "author",
        "extras",
        "field_id",
        "flag",
        "organization",
        "predicate",
        "name_prefix",
        "replicate_organization",
        "update_organization",
        "ckan_url",
    )

    profile_lists = zip_longest(*[tk.aslist(config.get(prefix + key)) for key in keys])

    for idx, item in enumerate(profile_lists):
        deprecated(
            f"Deprecated profile definition: {item}. Use"
            f" {PROFILE_PREFIX}*.OPTION form"
        )
        data = dict((k, v) for k, v in zip(keys, item) if v is not None)

        try:
            data["extras"] = json.loads(data.get("extras", "{}"))
        except (TypeError, ValueError):
            data["extras"] = {}
        yield Profile(id=str(idx), **data)

    yield from _parse_profiles(config)


def _parse_profiles(config: dict[str, str]) -> Iterable[Profile]:
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


def get_profiles() -> Iterator[Profile]:
    for profile in syndicate_configs_from_config(tk.config):
        yield prepare_profile_dict(profile)


def get_profile(id_: str) -> Optional[Profile]:
    for profile in get_profiles():
        if profile.id == id_:
            return profile


def try_sync(id_):
    deprecated("Use notify_sync or trigger_sync")
    notify_sync(id_)


def notify_sync(id_):
    plugin = get_plugin("syndicate")

    pkg = ckan_model.Package.get(id_)
    if not pkg:
        return
    plugin.notify(pkg, "changed")


def profiles_for(pkg: ckan_model.Package):
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


def get_target(url: str, apikey: str | None):
    """DEPRECATED. Get target CKAN instance."""
    deprecated(
        "`utils.get_targetd()` is deprecated since v2.2.2."
        + " Use Profile.get_target() instead."
    )
    ckan = ckanapi.RemoteCKAN(url, apikey=apikey)
    return ckan


def trigger_sync(id: str):
    package = ckan_model.Package.get(id)
    for profile in profiles_for(package):
        log.debug("Syndicate <{}> to {}".format(package.id, profile.ckan_url))
        syndicate_dataset(package.id, Topic.update, profile)
