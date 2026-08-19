from __future__ import annotations

import logging
from typing import Any

from ckan import model

from ckanext.syndicate import config, utils
from ckanext.syndicate.types import Topic

log = logging.getLogger(__name__)


def package_modification(sender: str, **kwargs: Any) -> None:
    """Handle the `action_succeeded` signal from package modifications.

    Track package create, update and delete actions to trigger syndication if
    it's enabled in config.
    """
    if not config.get_sync_on_changes():
        return
    result: dict[str, Any] | None = kwargs["result"]
    data_dict: dict[str, Any] = kwargs["data_dict"]
    # package_delete does not return any result
    id = result["id"] if result else data_dict["id"]
    package = model.Package.get(id)
    if not package:
        return

    topic = Topic.create if sender == "package_create" else Topic.update

    for profile in utils.profiles_for(package):
        log.debug("Syndicate on change triggered for <%s> to %s", package.id, profile.ckan_url)
        utils.syndicate_dataset(package.id, topic, profile)

    model.Session.commit()


def member_modification(sender: str, **kwargs: Any) -> None:
    """Handle the `action_succeeded` signal from member modifications.

    Track member create and delete actions to trigger syndication if dataset
    added to/removed from a group.
    """
    if not config.get_sync_on_member_changes():
        return

    data_dict: dict[str, Any] = kwargs["data_dict"]
    if data_dict["object_type"] != "package":
        return
    id = data_dict["object"]

    package = model.Package.get(id)
    if not package:
        return

    topic = Topic.update

    for profile in utils.profiles_for(package):
        log.debug("Syndicate on member change triggered for <%s> to %s", package.id, profile.ckan_url)
        utils.syndicate_dataset(package.id, topic, profile)

    model.Session.commit()
