from collections.abc import Callable
from typing import Any, cast

import pytest

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import model
from ckan.tests.helpers import call_action

from ckanext.syndicate import utils
from ckanext.syndicate.interfaces import ISyndicate
from ckanext.syndicate.logic.action import prepare_group_data
from ckanext.syndicate.types import Profile, Topic

TEST_PROFILE = "test"


@pytest.fixture
def syndicate(mocker):
    return mocker.patch("ckanext.syndicate.utils.syndicate_dataset")


class TestSyndicatePlugin(p.SingletonPlugin):
    p.implements(ISyndicate)

    def skip_syndication(self, package: model.Package, profile: Profile):
        return tk.asbool(package.extras.get("skip_me"))

    def prepare_package_for_syndication(
        self, package_id: str, data_dict: dict[str, Any], profile: Profile
    ) -> dict[str, Any]:
        data_dict["new_field"] = "custom value"

        return data_dict

    def prepare_group_for_syndication(self, group_id: str, group: dict[str, Any], profile: Profile) -> dict[str, Any]:
        group["new_field"] = "custom value"

        return group


@pytest.mark.usefixtures("with_plugins", "clean_db")
@pytest.mark.ckan_config("ckan.plugins", "syndicate test_syndicate")
class TestInterface:
    def test_custom_skip_logic(self, syndicate, package_factory: Callable[..., dict[str, Any]], mocker):
        package_factory(extras=[{"key": "skip_me", "value": "True"}])
        syndicate.assert_not_called()

    def test_custom_prepare_logic(self, package: dict[str, Any], mocker):
        profile = cast(Profile, utils.get_profile(TEST_PROFILE))
        profile.replicate_organization = False

        # mock to avoid request remote portal
        mocker.patch(
            "ckanext.syndicate.logic.action._compute_base_data_and_topic",
            return_value=(package, Topic.create),
        )

        result = call_action("syndicate_prepare", id=package["id"], profile=profile.id, topic="update")

        assert result["prepared"]["new_field"] == "custom value"

    def test_custom_prepare_group_logic(self, group: dict[str, Any], mocker):
        profile = cast(Profile, utils.get_profile(TEST_PROFILE))

        result = prepare_group_data(group["id"], group, profile)

        assert result["new_field"] == "custom value"
