from __future__ import annotations

import logging

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.common import CKANConfig
from ckan.model.domain_object import DomainObjectOperation

from ckanext.syndicate import config, utils
from ckanext.syndicate.interfaces import ISyndicate
from ckanext.syndicate.types import Topic

log = logging.getLogger(__name__)


@tk.blanket.blueprints
@tk.blanket.auth_functions
@tk.blanket.actions
@tk.blanket.cli
@tk.blanket.config_declarations
class SyndicatePlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IDomainObjectModification, inherit=True)
    p.implements(ISyndicate, inherit=True)

    # IConfigurer

    def update_config(self, config_: CKANConfig) -> None:
        tk.add_template_directory(config_, "templates")

    # IDomainObjectModification

    def notify(self, entity: model.DomainObject, operation: str | None = None):
        if (
            not config.get_sync_on_changes()
            or not operation  # This happens on IResourceURLChange
            or not isinstance(entity, model.Package)
        ):
            return

        _syndicate_dataset(entity, operation)


def _syndicate_dataset(package: model.Package, operation: str) -> None:
    if operation == DomainObjectOperation.new:
        topic = Topic.create
    elif operation == DomainObjectOperation.changed:
        topic = Topic.update
    else:
        log.debug(
            "Notification topic for operation [%s] is not defined",
            operation,
        )
        return

    for profile in utils.profiles_for(package):
        log.debug("Syndicate on change triggered for <%s> to %s", package.id, profile.ckan_url)
        utils.syndicate_dataset(package.id, topic, profile)
