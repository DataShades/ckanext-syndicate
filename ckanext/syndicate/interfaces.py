from __future__ import annotations

import logging
from typing import Any, Optional
import ckanapi
from werkzeug.utils import import_string

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.plugins import Interface

from .types import Profile

log = logging.getLogger(__name__)


class ISyndicate(Interface):
    def skip_syndication(
        self, package: model.Package, profile: Profile
    ) -> bool:
        """Decide whether a package must NOT be syndicated.

        Return `True` if package does not need syndication. Keep in mind, that
        non-syndicated package remains the same on the remote side. If package
        was removed locally, it's better not to skip syndication, so that it
        can be removed from the remote side.

        """
        if package.private:
            return True

        if profile.predicate:
            predicate = import_string(profile.predicate)
            if not predicate(package):
                log.info(
                    "Dataset[{}] will not syndicate because of predicate[{}]"
                    " rejection".format(package.id, profile.predicate)
                )
                return True

        syndicate = tk.asbool(package.extras.get(profile.flag, "false"))
        return not syndicate

    def prepare_package_for_syndication(
        self, package_id: str, data_dict: dict[str, Any], profile: Profile
    ) -> dict[str, Any]:
        """Make modifications of the dict that will be sent to remote portal.

        Remove all the sensitive fields, normalize package type, etc.

        """
        return data_dict

    def prepare_group_for_syndication(
        self, group_id: str, group: dict[str, Any], profile: Profile
    ) -> dict[str, Any]:
        """Make modifications of the dict that will be sent to remote portal.

        Remove all the sensitive fields, normalize group/organization type, etc.

        """
        return group

    def syndicate_reattach_on_error(self, error: Exception) -> bool:
        """Decide if the remote package should be re-attached during syndication.

        This method called when syndication makes an attempt to create a
        package, while it already exists on remote portal. Usually it means,
        that `Profile.field_id` is not properly configured and local package
        just lost the details about it remote version. So the ID of the remote
        package must be added to the local package in order to create a
        relationship between them.

        But this method can also be called if some other error happened during
        syndication. By default, syndication just checks the error, and if it's
        an validation error complaining on the `name` field, re-attaching
        happens. Otherwile, error raised further.

        If the remote portal uses the language different from english, or error
        messages are customized, default logic fails to identify related
        package. In such a case you can redefine this method and provide better
        mechanism for checking errors.

        """
        if not isinstance(error, ckanapi.ValidationError):
            return False

        return "That URL is already in use." in error.error_dict.get(
            "name", []
        )
