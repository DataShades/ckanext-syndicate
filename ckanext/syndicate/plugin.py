from __future__ import annotations

import logging

import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.model.domain_object import DomainObjectOperation

from . import cli, utils
from .interfaces import ISyndicate
from .logic import action, auth
from .types import Topic

log = logging.getLogger(__name__)

CONFIG_SYNC_ON_CHANGES = "ckanext.syndicate.sync_on_changes"
DEFAULT_SYNC_ON_CHANGES = True


class SyndicatePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IDomainObjectModification, inherit=True)
    plugins.implements(plugins.IClick)
    plugins.implements(ISyndicate, inherit=True)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)

    # IActions

    def get_actions(self):
        return action.get_actions()

    # IAuthFunctions

    def get_auth_functions(self):
        return auth.get_auth_functions()

    # IClick

    def get_commands(self):
        return cli.get_commands()

    # Based on ckanext-webhooks plugin
    # IDomainObjectNotification & IResourceURLChange
    def notify(self, entity, operation=None):
        sync_on_changes = tk.asbool(
            tk.config.get(CONFIG_SYNC_ON_CHANGES, DEFAULT_SYNC_ON_CHANGES)
        )

        # Handle only Package entities
        if not isinstance(entity, model.Package):
            return

        # Process deletions or other operations when they occur
        if entity.state == "deleted" or (operation and sync_on_changes):
            _syndicate_dataset(entity, operation)


def _get_topic(operation: str) -> Topic:
    if operation == DomainObjectOperation.new:
        return Topic.create

    if operation == DomainObjectOperation.changed:
        return Topic.update

    return Topic.unknown


def _syndicate_dataset(package, operation):
    topic = _get_topic(operation)
    if topic is Topic.unknown:
        log.debug(
            "Notification topic for operation [%s] is not defined",
            operation,
        )
        return

    for profile in utils.profiles_for(package):
        log.debug("Syndicate <{}> to {}".format(package.id, profile.ckan_url))
        utils.syndicate_dataset(package.id, topic, profile)
