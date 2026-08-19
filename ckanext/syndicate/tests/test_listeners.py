from collections.abc import Callable
from typing import Any

import pytest

from ckan.tests.helpers import call_action

from ckanext.syndicate.config import CONFIG_SYNC_ON_CHANGES
from ckanext.syndicate.types import Topic


@pytest.fixture
def syndicate(mocker):
    return mocker.patch("ckanext.syndicate.utils.syndicate_dataset")


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestSyndicateOnPackageChangeListener:
    def test_syndicate_on_create(self, syndicate, package_factory: Callable[..., dict[str, Any]], mocker):
        dataset = package_factory(extras=[{"key": "syndicate", "value": "True"}])
        syndicate.assert_called_with(dataset["id"], Topic.create, mocker.ANY)

    def test_syndicate_on_update(self, syndicate, package_factory: Callable[..., dict[str, Any]], mocker):
        dataset = package_factory(extras=[{"key": "syndicate", "value": "True"}])
        syndicate.reset_mock()

        call_action("package_patch", id=dataset["id"], name="updated-name")
        syndicate.assert_called_with(dataset["id"], Topic.update, mocker.ANY)

    def test_syndicate_on_delete(self, syndicate, package_factory: Callable[..., dict[str, Any]]):
        dataset = package_factory(extras=[{"key": "syndicate", "value": "True"}])
        syndicate.reset_mock()

        call_action("package_delete", id=dataset["id"])
        assert not syndicate.called

    @pytest.mark.ckan_config(CONFIG_SYNC_ON_CHANGES, False)
    def test_sync_on_change_disabled(self, syndicate, package_factory: Callable[..., dict[str, Any]]):
        package_factory(extras=[{"key": "syndicate", "value": "True"}])

        assert not syndicate.called


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestSyndicateOnResourceChangeListener:
    def test_syndicate_on_resource_create(self, syndicate, package_factory: Callable[..., dict[str, Any]], mocker):
        dataset = package_factory(extras=[{"key": "syndicate", "value": "True"}])

        call_action("resource_create", package_id=dataset["id"], url="http://xxx", name="xxx")

        assert syndicate.call_count == 2
        syndicate.assert_called_with(dataset["id"], Topic.update, mocker.ANY)

    def test_syndicate_on_resource_update(self, syndicate, package_factory: Callable[..., dict[str, Any]], mocker):
        dataset = package_factory(extras=[{"key": "syndicate", "value": "True"}])

        resource = call_action("resource_create", package_id=dataset["id"], url="http://xxx", name="xxx")
        syndicate.reset_mock()

        call_action(
            "resource_update",
            id=resource["id"],
            package_id=dataset["id"],
            url="http://yyy",
            name="yyy",
        )

        assert syndicate.call_count == 1
        syndicate.assert_called_with(dataset["id"], Topic.update, mocker.ANY)

    def test_syndicate_on_resource_delete(self, syndicate, package_factory: Callable[..., dict[str, Any]], mocker):
        dataset = package_factory(extras=[{"key": "syndicate", "value": "True"}])

        resource = call_action("resource_create", package_id=dataset["id"], url="http://xxx", name="xxx")
        syndicate.reset_mock()

        call_action(
            "resource_delete",
            id=resource["id"],
            package_id=dataset["id"],
        )

        assert syndicate.call_count == 1
        syndicate.assert_called_with(dataset["id"], Topic.update, mocker.ANY)


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestSyndicationSkipLogic:
    def test_skip_private_dataset(self, syndicate, package_factory: Callable[..., dict[str, Any]], mocker):
        package_factory(extras=[{"key": "syndicate", "value": "True"}], private=True)
        assert not syndicate.called

    def test_skip_without_flag(self, syndicate, package_factory: Callable[..., dict[str, Any]]):
        package_factory()
        assert not syndicate.called

    def test_skip_flag_false(self, syndicate, package_factory: Callable[..., dict[str, Any]]):
        package_factory(extras=[{"key": "syndicate", "value": "false"}])
        assert not syndicate.called
