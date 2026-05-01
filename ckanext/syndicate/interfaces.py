from __future__ import annotations

import logging
from typing import Any

import ckan.plugins.toolkit as tk
from ckan import model
from ckan.plugins import Interface

from .types import Profile

log = logging.getLogger(__name__)


class ISyndicate(Interface):
    def skip_syndication(self, package: model.Package, profile: Profile) -> bool | str:
        """Decide whether a package must NOT be syndicated.

        Return `True` or non-empty string if package does not need
        syndication. Keep in mind, that non-syndicated package remains the same
        on the remote side. If package was removed locally, it's better not to
        skip syndication, so that it can be removed from the remote side.

        Returned string will be printed in application logs and may clarify
        reasons behind syndication flow. Prefer returning string instead of uninformative `True`
        """
        if package.private:
            return "package is private"

        if not tk.asbool(package.extras.get(profile.flag, "false")):
            return "syndication flag disabled on package"

        return False

    def prepare_package_for_syndication(
        self, package_id: str, data_dict: dict[str, Any], profile: Profile
    ) -> dict[str, Any]:
        """Make modifications of the dict that will be sent to remote portal.

        Remove all the sensitive fields, normalize package type, etc.
        """
        return data_dict

    def prepare_group_for_syndication(self, group_id: str, group: dict[str, Any], profile: Profile) -> dict[str, Any]:
        """Make modifications of the dict that will be sent to remote portal.

        Remove all the sensitive fields, normalize group/organization type, etc.
        """
        return group
