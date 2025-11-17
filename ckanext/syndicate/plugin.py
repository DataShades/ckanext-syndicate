from __future__ import annotations

import logging

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan.common import CKANConfig
from ckan.types import SignalMapping

from ckanext.syndicate.interfaces import ISyndicate
from ckanext.syndicate.listeners import action_succeeded_listener

log = logging.getLogger(__name__)


@tk.blanket.blueprints
@tk.blanket.auth_functions
@tk.blanket.actions
@tk.blanket.cli
@tk.blanket.config_declarations
class SyndicatePlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(ISyndicate, inherit=True)
    p.implements(p.ISignal, inherit=True)

    # IConfigurer

    def update_config(self, config_: CKANConfig) -> None:
        tk.add_template_directory(config_, "templates")

    # ISignal

    def get_signal_subscriptions(self) -> SignalMapping:
        return {tk.signals.action_succeeded: [action_succeeded_listener]}
