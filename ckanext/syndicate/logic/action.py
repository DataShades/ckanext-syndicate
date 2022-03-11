from __future__ import annotations

import contextlib
import logging
import uuid
from typing import Any, Optional


import requests
import ckanapi

import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from ckan.logic import validate
from ckan import model
from ckan.lib.search import rebuild

from . import schema
from .. import types, signals, utils
from ..interfaces import ISyndicate


log = logging.getLogger(__name__)


def get_actions():
    return {
        "syndicate_sync": sync,
        "syndicate_prepare": prepare,
        "syndicate_sync_organization": sync_organization,
        "syndicate_sync_group": sync_group,
    }


@validate(schema.sync)
def sync(context, data_dict):
    tk.check_access("syndicate_sync", context, data_dict)

    details = tk.get_action("syndicate_prepare")(
        context,
        {
            "id": data_dict["id"],
            "topic": data_dict["topic"].name,
            "profile": data_dict["profile"].id,
        },
    )
    ckan = utils.get_target(
        data_dict["profile"].ckan_url, data_dict["profile"].api_key
    )

    _notify_before(
        data_dict["id"], data_dict["profile"], {"id": data_dict["id"]}
    )

    with reattaching_context(
        details["package"]["id"],
        details["prepared"],
        data_dict["profile"],
        ckan,
    ):
        if types.Topic[details["topic"]] is types.Topic.create:
            result = ckan.action.package_create(**details["prepared"])
            set_syndicated_id(
                details["package"]["id"],
                result["id"],
                data_dict["profile"].field_id,
            )

        else:
            result = ckan.action.package_update(**details["prepared"])

    _notify_after(
        data_dict["id"], data_dict["profile"], {"id": data_dict["id"]}
    )

    return {"id": data_dict["id"]}


@validate(schema.prepare)
def prepare(context, data_dict):
    tk.check_access("syndicate_prepare", context, data_dict)
    package: dict[str, Any] = tk.get_action("package_show")(
        {
            "user": context["user"],
            "ignore_auth": context.get("ignore_auth", False),
            "use_cache": False,
            "validate": False,
        },
        {"id": data_dict["id"]},
    )

    ckan = utils.get_target(
        data_dict["profile"].ckan_url, data_dict["profile"].api_key
    )

    if data_dict[
        "topic"
    ] is types.Topic.update and not tk.h.get_pkg_dict_extra(
        package, data_dict["profile"].field_id
    ):
        data_dict["topic"] = types.Topic.create

    base, topic = _compute_base_data_and_topic(
        package, data_dict["topic"], data_dict["profile"], ckan
    )

    org = base.pop("organization")
    if data_dict["profile"].replicate_organization:
        base["owner_org"] = tk.get_action("syndicate_sync_organization")(
            context,
            {
                "id": org["id"],
                "profile": data_dict["profile"].id,
                "skip_existing": True,
            },
        )
    else:
        base["owner_org"] = data_dict["profile"].organization

    prepared = _prepare(package["id"], base, data_dict["profile"])

    return {"package": package, "prepared": prepared, "topic": topic.name}


@validate(schema.sync_organization)
def sync_organization(context, data_dict):
    _group_or_org_sync(context, data_dict, True)


@validate(schema.sync_group)
def sync_group(context, data_dict):
    _group_or_org_sync(context, data_dict, False)


def _group_or_org_sync(
    context: dict[str, Any], data_dict: dict[str, Any], is_org: bool
):
    type_ = "organization" if is_org else "group"
    group = tk.get_action(type_ + "_show")(context, {"id": data_dict["id"]})
    profile: types.Profile = data_dict["profile"]

    ckan = utils.get_target(profile.ckan_url, profile.api_key)
    remote_group = None

    show = getattr(ckan.action, type_ + "_show")
    try:
        remote_group = show(id=group["name"])
    except ckanapi.NotFound:
        log.error(
            "%s not found, creating new %s.",
            group["name"],
            "Organization" if is_org else "Group",
        )
    except (ckanapi.NotAuthorized, ckanapi.CKANAPIError) as e:
        log.error("Replication error(trying to continue): {}".format(e))
    except Exception as e:
        log.error("Replication error: {}".format(e))
        raise

    if data_dict["skip_existing"] and remote_group:
        return remote_group["id"]

    local_id = group.pop("id")
    if not remote_group:
        action = getattr(ckan.action, type_ + "_create")
    else:
        group["id"] = remote_group["id"]
        action = getattr(ckan.action, type_ + "_update")

    group.pop("image_url", None)
    group.pop("num_followers", None)
    group.pop("tags", None)
    group.pop("users", None)
    group.pop("groups", None)

    default_img_url = "https://www.gravatar.com/avatar/123?s=400&d=identicon"
    image_url = group.pop("image_display_url", default_img_url)
    image_fd = requests.get(image_url, stream=True, timeout=2).raw
    group.update(image_upload=image_fd)

    for plugin in plugins.PluginImplementations(ISyndicate):
        group = plugin.prepare_group_for_syndication(local_id, group, profile)

    remote_group = action(**group)

    return remote_group["id"]


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
        syndicated_id: Optional[str] = tk.h.get_pkg_dict_extra(
            package, profile.field_id
        )
        if not syndicated_id:
            return _compute_base_data_and_topic(
                package, types.Topic.create, profile, ckan
            )

        try:
            remote_package = ckan.action.package_show(id=syndicated_id)
        except ckanapi.NotFound:
            return _compute_base_data_and_topic(
                package, types.Topic.create, profile, ckan
            )

        # Keep the existing remote ID and Name
        base["id"] = remote_package["id"]
        base["name"] = remote_package["name"]

    return base, topic


def _notify_before(
    package_id: str, profile: types.Profile, params: dict[str, Any]
):
    try:
        tk.get_action("before_syndication_action")(
            {"profile": profile}, params
        )
    except KeyError:
        pass
    else:
        utils.deprecated(
            "before_syndication_action is deprecated in v2.0.0. Use"
            " before_syndication signal instead"
        )
    signals.before_syndication.send(package_id, profile=profile, params=params)


def _notify_after(
    package_id: str, profile: types.Profile, params: dict[str, Any]
):
    try:
        tk.get_action("after_syndication_action")({"profile": profile}, params)
    except KeyError:
        pass
    else:
        utils.deprecated(
            "after_syndication_action is deprecated in v2.0.0. Use"
            " after_syndication signal instead"
        )
    signals.after_syndication.send(package_id, profile=profile, params=params)


def _compute_remote_name(package: dict[str, Any], profile: types.Profile):
    name = package["name"]
    if profile.name_prefix:
        name = "%s-%s" % (
            profile.name_prefix,
            name,
        )

    if len(name) > 100:
        uniq = str(uuid.uuid3(uuid.NAMESPACE_DNS, name))
        name = name[:92] + uniq[:8]
    return name


@contextlib.contextmanager
def reattaching_context(
    local_id: str,
    package: dict[str, Any],
    profile: types.Profile,
    ckan: ckanapi.RemoteCKAN,
):
    try:
        yield
    except ckanapi.ValidationError as e:
        if "That URL is already in use." not in e.error_dict.get("name", []):
            raise
    else:
        return

    log.warning(
        "There is a package with the same name on remote portal: %s.",
        package["name"],
    )
    author = profile.author
    if not author:
        log.error(
            "Profile %s does not have author set. Skip syndication", profile.id
        )
        return

    try:
        remote_package = ckan.action.package_show(id=package["name"])
    except ckanapi.NotFound:
        log.error(
            "Current user does not have access to read remote package. Skip"
            " syndication"
        )
        return

    try:
        remote_user = ckan.action.user_show(id=author)
    except ckanapi.NotFound:
        log.error(
            'User "{0}" not found on remote portal. Skip syndication'.format(
                author
            )
        )
        return

    if remote_package["creator_user_id"] != remote_user["id"]:
        log.error(
            "Creator of remote package %s did not match '%s(%s)'. Skip"
            " syndication",
            remote_package["creator_user_id"],
            author,
            remote_user["id"],
        )
        return

    log.info("Author is the same({0}). Continue syndication".format(author))

    ckan.action.package_update(id=remote_package["id"], **package)
    set_syndicated_id(
        local_id,
        remote_package["id"],
        profile.field_id,
    )


def set_syndicated_id(local_id: str, remote_id: str, field: str):
    """Set the remote package id on the local package"""
    ext_id = (
        model.Session.query(model.PackageExtra.id)
        .join(model.Package, model.Package.id == model.PackageExtra.package_id)
        .filter(
            model.Package.id == local_id,
            model.PackageExtra.key == field,
        )
        .first()
    )
    if not ext_id:
        existing = model.PackageExtra(
            package_id=local_id,
            key=field,
            value=remote_id,
        )
        model.Session.add(existing)
        model.Session.commit()
        model.Session.flush()
    else:
        model.Session.query(model.PackageExtra).filter_by(id=ext_id).update(
            {"value": remote_id, "state": "active"}
        )
    rebuild(local_id)


def _prepare(
    local_id: str, package: dict[str, Any], profile: types.Profile
) -> dict[str, Any]:
    extras_dict = dict([(o["key"], o["value"]) for o in package["extras"]])

    extras_dict.pop(profile.field_id, None)
    package["extras"] = [
        {"key": k, "value": v} for (k, v) in extras_dict.items()
    ]

    package["resources"] = [
        {"url": r["url"], "name": r["name"]} for r in package["resources"]
    ]

    try:
        package = tk.get_action("update_dataset_for_syndication")(
            {},
            {"dataset_dict": package, "package_id": local_id},
        )
    except KeyError:
        pass
    else:
        utils.deprecated(
            "update_dataset_for_syndication is deprecated. Implement"
            " ISyndicate instead"
        )
    for plugin in plugins.PluginImplementations(ISyndicate):
        package = plugin.prepare_package_for_syndication(
            local_id, package, profile
        )

    return package
