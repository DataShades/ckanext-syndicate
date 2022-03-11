from __future__ import annotations

import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ..interfaces import ISyndicate


class TestSyndicatePlugin(p.SingletonPlugin):
    p.implements(ISyndicate)

    def skip_syndication(self, package, profile):
        return tk.asbool(
            tk.config.get("ckanext.test_syndicate.skip_syndication")
        )

    def prepare_package_for_syndication(self, package_id, data_dict, profile):

        data_dict["extras"].append({"key": "test_syndicate", "value": None})
        return data_dict
