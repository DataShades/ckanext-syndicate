from __future__ import annotations

import logging
import uuid
from typing import Any

import ckanapi
import requests
from typing_extensions import TypedDict

import ckan.plugins.toolkit as tk
from ckan import plugins as p
from ckan import types as ckan_types
from ckan.logic import validate

from ckanext.syndicate import signals, types
from ckanext.syndicate.interfaces import ISyndicate
from ckanext.syndicate.logic import schema
from ckanext.syndicate.model import SyndicationLog

log = logging.getLogger(__name__)
REMOTE_NAME_MAX_LENGTH = 100
GROUP_EXCLUDE_FIELDS = [
    "is_organization",
    "num_followers",
    "display_name",
    "package_count",
    "tags",
    "users",
    "groups",
    "extras",
]


class SyncData(TypedDict):
    id: str
    topic: types.Topic
    profile: types.Profile


class SyncResult(TypedDict):
    local_id: str
    target_id: str
    state: str
    error: str | None


@validate(schema.syndicate_sync)  # type: ignore
def syndicate_sync(context: ckan_types.Context, data_dict: SyncData) -> SyncResult:
    tk.check_access("syndicate_sync", context, data_dict)  # type: ignore

    details = tk.get_action("syndicate_prepare")(
        context,
        {
            "id": data_dict["id"],
            "topic": data_dict["topic"].name,
            "profile": data_dict["profile"].id,
        },
    )
    ckan = data_dict["profile"].get_target()

    signals.before_syndication.send(data_dict["id"], profile=data_dict["profile"], details=details)

    result = None
    topic = types.Topic[details["topic"]]

    try:
        if topic is types.Topic.create:
            result = ckan.action.package_create(**details["prepared"])
        else:
            result = ckan.action.package_update(**details["prepared"])
    except Exception as e:  # noqa: BLE001
        SyndicationLog.write(
            local_id=data_dict["id"],
            profile_id=data_dict["profile"].id,
            state=SyndicationLog.State.FAILED,
            error=str(e),
        )

        return SyncResult(
            local_id=data_dict["id"],
            target_id="",
            error=str(e),
            state=SyndicationLog.State.FAILED,
        )

    signals.after_syndication.send(data_dict["id"], profile=data_dict["profile"], remote=result)

    SyndicationLog.write(
        local_id=data_dict["id"],
        target_id=result["id"],
        profile_id=data_dict["profile"].id,
    )

    return SyncResult(
        local_id=data_dict["id"],
        target_id=result["id"],
        error=None,
        state=SyndicationLog.State.SYNCED,
    )


@validate(schema.syndicate_prepare)  # type: ignore
def syndicate_prepare(context: ckan_types.Context, data_dict: SyncData):
    tk.check_access("syndicate_prepare", context, data_dict)  # type: ignore

    package: dict[str, Any] = tk.get_action("package_show")(
        {
            "user": context.get("user", ""),
            "ignore_auth": context.get("ignore_auth", False),
            "use_cache": False,
            "validate": False,
        },
        {"id": data_dict["id"]},
    )

    ckan = data_dict["profile"].get_target()

    if data_dict["topic"] is types.Topic.update and not SyndicationLog.get(package["id"], data_dict["profile"].id):
        data_dict["topic"] = types.Topic.create

    base, topic = _compute_base_data_and_topic(package, data_dict["topic"], data_dict["profile"], ckan)

    org = base.pop("organization")

    if data_dict["profile"].replicate_organization or data_dict["profile"].update_organization:
        base["owner_org"] = tk.get_action("syndicate_sync_organization")(
            context,
            {
                "id": org["id"],
                "profile": data_dict["profile"].id,
                "update_existing": data_dict["profile"].update_organization,
            },
        )
    else:
        base["owner_org"] = data_dict["profile"].organization

    prepared = _prepare(package["id"], base, data_dict["profile"])

    return {"package": package, "prepared": prepared, "topic": topic.name}


def _prepare(local_id: str, package: dict[str, Any], profile: types.Profile) -> dict[str, Any]:
    extras_dict = {o["key"]: o["value"] for o in package["extras"]}
    extras_dict.pop(profile.field_id, None)

    package["extras"] = [{"key": k, "value": v} for (k, v) in extras_dict.items()]
    package["resources"] = [{"url": r["url"], "name": r["name"]} for r in package["resources"]]

    for plugin in p.PluginImplementations(ISyndicate):
        package = plugin.prepare_package_for_syndication(local_id, package, profile)

    return package


@validate(schema.sync_organization)
def syndicate_sync_organization(context: ckan_types.Context, data_dict: ckan_types.DataDict):
    return _group_or_org_sync(context, data_dict, True)


@validate(schema.sync_group)
def syndicate_sync_group(context: ckan_types.Context, data_dict: ckan_types.DataDict):
    return _group_or_org_sync(context, data_dict, False)


def _group_or_org_sync(context: ckan_types.Context, data_dict: dict[str, Any], is_org: bool):
    type_ = "organization" if is_org else "group"
    group = tk.get_action(type_ + "_show")(context, {"id": data_dict["id"]})
    profile: types.Profile = data_dict["profile"]

    ckan = profile.get_target()
    remote_group = None

    show = getattr(ckan.action, type_ + "_show")
    try:
        remote_group = show(id=group["name"])
    except ckanapi.NotFound:
        log.warning(
            "%s not found, creating new %s.",
            group["name"],
            "Organization" if is_org else "Group",
        )
    except (ckanapi.NotAuthorized, ckanapi.CKANAPIError) as e:
        log.warning("Replication error (trying to continue): {%s}", e)
    except Exception:
        log.exception("Replication error")
        raise

    if not data_dict["update_existing"] and remote_group:
        return remote_group["id"]

    local_id = group.pop("id")

    if not remote_group:
        action = getattr(ckan.action, f"{type_}_create")
    else:
        group["id"] = remote_group["id"]
        action = getattr(ckan.action, f"{type_}_update")

    group = prepare_group_data(local_id, group, profile)

    signals.before_group_syndication.send(local_id, profile=profile, details=group)
    remote_group = action(**group)
    signals.after_group_syndication.send(local_id, profile=profile, remote=remote_group)

    return remote_group["id"]


def prepare_group_data(local_id: str, group: dict[str, Any], profile: types.Profile) -> dict[str, Any]:
    for field in GROUP_EXCLUDE_FIELDS:
        group.pop(field, None)

    if profile.upload_organization_image:
        group.pop("image_url", None)
        default_img_url = "https://www.gravatar.com/avatar/123?s=400&d=identicon"
        image_url = group.pop("image_display_url") or default_img_url
        image_fd = requests.get(image_url, stream=True, timeout=2).raw
        group.update(image_upload=image_fd)

    for plugin in p.PluginImplementations(ISyndicate):
        group = plugin.prepare_group_for_syndication(local_id, group, profile)

    return group


def _compute_base_data_and_topic(
    package: dict[str, Any],
    topic: types.Topic,
    profile: types.Profile,
    ckan: ckanapi.RemoteCKAN,
) -> tuple[dict[str, Any], types.Topic]:
    base = dict(package)

    if topic is types.Topic.create:
        del base["id"]
        base["name"] = _compute_remote_name(package, profile)

    else:
        syndicate_record = SyndicationLog.get(package["id"], profile.id)
        if not syndicate_record:
            return _compute_base_data_and_topic(package, types.Topic.create, profile, ckan)

        try:
            remote_package = ckan.action.package_show(id=syndicate_record.target_id)
        except ckanapi.NotFound:
            return _compute_base_data_and_topic(package, types.Topic.create, profile, ckan)

        # Keep the existing remote ID and Name
        base["id"] = remote_package["id"]
        if not profile.refresh_package_name:
            base["name"] = remote_package["name"]

    return base, topic


def _compute_remote_name(package: dict[str, Any], profile: types.Profile) -> str:
    name = package["name"]

    if profile.name_prefix:
        name = f"{profile.name_prefix}-{name}"

    if len(name) > REMOTE_NAME_MAX_LENGTH:
        uniq = str(uuid.uuid3(uuid.NAMESPACE_DNS, name))
        name = name[:92] + uniq[:8]
    return name
