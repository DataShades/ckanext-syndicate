from __future__ import annotations

import logging
from typing import Any

from ckan import model

from ckanext.syndicate import config, utils
from ckanext.syndicate.types import Topic

log = logging.getLogger(__name__)


def action_succeeded_listener(sender: str, **kwargs: Any) -> None:
    """Handle the `action_succeeded` signal.

    Track package create and update actions to trigger syndication
    on package create/update if enabled in config.
    """
    if sender not in ("package_create", "package_update") or not config.get_sync_on_changes():
        return

    package = model.Package.get(kwargs["result"]["id"])

    if not package:
        return

    topic = Topic.create if sender == "package_create" else Topic.update

    for profile in utils.profiles_for(package):
        log.debug("Syndicate on change triggered for <%s> to %s", package.id, profile.ckan_url)
        utils.syndicate_dataset(package.id, topic, profile)
