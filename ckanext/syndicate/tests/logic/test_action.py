import pytest

import ckanapi
import ckan.plugins.toolkit as tk

from ckan.tests.helpers import call_action
from ckanext.syndicate.utils import get_profiles


@pytest.fixture
def remote_org(organization_factory, user, monkeypatch, ckan_config):

    org = organization_factory(
        users=[{"capacity": "editor", "name": user["id"]}],
    )
    monkeypatch.setitem(
        ckan_config, "ckanext.syndicate.profile.test.organization", org["name"]
    )
    return org


@pytest.mark.usefixtures("clean_db", "ckan")
@pytest.mark.ckan_config("ckanext.syndicate.profile.test.name_prefix", "test")
class TestPrepare(object):
    def test_prepare_default(self, package, remote_org):
        prepared = call_action(
            "syndicate_prepare",
            id=package["id"],
            topic="create",
            profile=next(get_profiles()).id,
        )
        assert prepared["topic"] == "create"
        assert prepared["package"] == package

        expected = {
            **package,
            "owner_org": remote_org["name"],
            "name": "test-" + package["name"],
        }
        expected.pop("id")
        expected.pop("organization")

        assert prepared["prepared"] == expected


@pytest.mark.usefixtures("clean_db", "ckan", "with_request_context")
@pytest.mark.ckan_config("ckanext.syndicate.profile.test.name_prefix", "test")
class TestSync(object):
    def test_create_package(
        self, create_with_upload, package_factory, remote_org
    ):
        dataset = package_factory(
            extras=[{"key": "syndicate", "value": "true"}],
        )
        syndicated_id = tk.h.get_pkg_dict_extra(dataset, "syndicated_id")
        assert syndicated_id is None

        create_with_upload("test", "test_file.txt", package_id=dataset["id"])
        create_with_upload("test", "test_file1.txt", package_id=dataset["id"])

        call_action(
            "syndicate_sync",
            id=dataset["id"],
            topic="create",
            profile=next(get_profiles()).id,
        )

        # Reload our local package, to read the syndicated ID
        source = call_action("package_show", id=dataset["id"])
        syndicated_id = tk.h.get_pkg_dict_extra(source, "syndicated_id")
        assert syndicated_id is not None

        # Expect a new package to be created
        syndicated = call_action("package_show", id=syndicated_id)
        assert syndicated["id"] == syndicated_id
        assert syndicated["name"] == "test-" + source["name"]
        assert syndicated["owner_org"] == remote_org["id"]
        assert syndicated["notes"] == source["notes"]

        # Test links to resources on the source CKAN instace have been added
        resources = syndicated["resources"]
        assert len(resources) == 2
        for idx, resource in enumerate(resources):
            assert source["resources"][idx]["url"] == resource["url"]

    def test_update_package(
        self, remote_org, create_with_upload, package_factory
    ):
        # Create a dummy remote dataset
        syndicated_id = package_factory()["id"]

        # Create the local syndicated dataset, pointing to the dummy remote
        dataset = package_factory(
            extras=[
                {"key": "syndicate", "value": "true"},
                {"key": "syndicated_id", "value": syndicated_id},
            ]
        )
        local_resource = create_with_upload(
            "test", "test_file.txt", package_id=dataset["id"]
        )

        call_action(
            "syndicate_sync",
            id=dataset["id"],
            topic="update",
            profile=next(get_profiles()).id,
        )

        # Expect the remote package to be updated
        syndicated = call_action("package_show", id=syndicated_id)
        assert syndicated["id"] == syndicated_id
        assert syndicated["owner_org"] == remote_org["id"]

        # Test the local the local resources URL has been updated
        resources = syndicated["resources"]
        assert len(resources) == 1
        remote_resource_url = resources[0]["url"]
        local_resource_url = local_resource["url"]
        assert local_resource_url == remote_resource_url

    def test_syndicate_existing_package_with_stale_syndicated_id(
        self, package_factory
    ):
        stale = package_factory(
            extras=[
                {"key": "syndicate", "value": "true"},
                {
                    "key": "syndicated_id",
                    "value": "87f7a229-46d0-4171-bfb6-048c622adcdc",
                },
            ]
        )

        call_action(
            "syndicate_sync",
            id=stale["id"],
            topic="update",
            profile=next(get_profiles()).id,
        )

        updated = call_action("package_show", id=stale["id"])
        syndicated_id = tk.h.get_pkg_dict_extra(updated, "syndicated_id")

        # assert syndicated_id != tk.h.get_pkg_dict_extra(stale, "syndicated_id")

        syndicated = call_action("package_show", id=syndicated_id)
        assert syndicated["notes"] == updated["notes"]

    @pytest.mark.ckan_config("ckan.syndicate.replicate_organization", "yes")
    def test_organization_replication(
        self, ckan, user, organization_factory, package_factory, mocker
    ):
        local_org = organization_factory(
            users=[{"capacity": "editor", "name": user["id"]}]
        )
        dataset = package_factory(
            owner_org=local_org["id"],
            extras=[{"key": "syndicate", "value": "true"}],
        )

        ckan.address = "http://example.com"

        # Syndicate to our Test CKAN instance
        mock_org_create = mocker.Mock()
        mock_org_show = mocker.Mock()
        mock_org_show.side_effect = ckanapi.NotFound
        mock_org_create.return_value = local_org

        ckan.action.organization_create = mock_org_create
        ckan.action.organization_show = mock_org_show

        call_action(
            "syndicate_sync",
            id=dataset["id"],
            topic="create",
            profile=next(get_profiles()).id,
        )
        mock_org_show.assert_called_once_with(id=local_org["name"])

        assert mock_org_create.called

    @pytest.mark.ckan_config("ckan.syndicate.update_organization", "true")
    def test_organization_update_true(
        self, ckan, user, organization_factory, package_factory, mocker
    ):
        """If ckan.syndicate.update_organization set to true, we're updating
        organization"""
        local_org = organization_factory(
            users=[{"capacity": "editor", "name": user["id"]}]
        )
        dataset = package_factory(
            owner_org=local_org["id"],
            extras=[{"key": "syndicate", "value": "true"}],
        )

        mock_org_create = mocker.Mock()
        mock_org_show = mocker.Mock()
        mock_org_update = mocker.Mock()

        mock_org_show.side_effect = ckanapi.NotFound
        mock_org_create.return_value = local_org
        mock_org_update.return_value = local_org

        ckan.action.organization_create = mock_org_create
        ckan.action.organization_show = mock_org_show
        ckan.action.organization_update = mock_org_update

        profile = next(get_profiles())

        call_action(
            "syndicate_sync",
            id=dataset["id"],
            topic="create",
            profile=profile.id,
        )
        mock_org_show.assert_called_once_with(id=local_org["name"])

        assert mock_org_create.called
        assert not mock_org_update.called

        mock_org_show = mocker.Mock()
        mock_org_show.return_value = local_org
        ckan.action.organization_show = mock_org_show

        call_action(
            "syndicate_sync_organization",
            id=local_org["id"],
            profile=profile.id,
            update_existing=profile.update_organization,
        )

        assert mock_org_update.called

    @pytest.mark.ckan_config("ckan.syndicate.replicate_organization", "true")
    @pytest.mark.ckan_config("ckan.syndicate.update_organization", "false")
    def test_organization_update_false(
        self, ckan, user, organization_factory, package_factory, mocker
    ):
        """If ckan.syndicate.update_organization set to false, we're not updating
        organization"""
        local_org = organization_factory(
            users=[{"capacity": "editor", "name": user["id"]}]
        )
        dataset = package_factory(
            owner_org=local_org["id"],
            extras=[{"key": "syndicate", "value": "true"}],
        )

        mock_org_create = mocker.Mock()
        mock_org_show = mocker.Mock()
        mock_org_update = mocker.Mock()

        mock_org_show.side_effect = ckanapi.NotFound
        mock_org_create.return_value = local_org
        mock_org_update.return_value = local_org

        ckan.action.organization_create = mock_org_create
        ckan.action.organization_show = mock_org_show
        ckan.action.organization_update = mock_org_update

        profile = next(get_profiles())

        call_action(
            "syndicate_sync",
            id=dataset["id"],
            topic="create",
            profile=profile.id,
        )

        mock_org_show.assert_called_once_with(id=local_org["name"])

        assert mock_org_create.called
        assert not mock_org_update.called

        mock_org_show = mocker.Mock()
        mock_org_show.return_value = local_org
        ckan.action.organization_show = mock_org_show

        call_action(
            "syndicate_sync_organization",
            id=local_org["id"],
            profile=profile.id,
            update_existing=profile.update_organization,
        )

        assert not mock_org_update.called

    @pytest.mark.ckan_config("ckan.syndicate.name_prefix", "test")
    def test_author_check(
        self, user, ckan, monkeypatch, ckan_config, package_factory, mocker
    ):
        monkeypatch.setitem(ckan_config, "ckan.syndicate.author", user["name"])

        dataset = package_factory(
            extras=[{"key": "syndicate", "value": "true"}]
        )

        mock_user_show = mocker.Mock()
        mock_user_show.return_value = user

        ckan.action.user_show = mock_user_show

        call_action(
            "syndicate_sync",
            id=dataset["id"],
            topic="create",
            profile=next(get_profiles()).id,
        )
        call_action(
            "package_patch",
            id=dataset["id"],
            extras=[{"key": "syndicate", "value": "true"}],
        )

        call_action(
            "syndicate_sync",
            id=dataset["id"],
            topic="update",
            profile=next(get_profiles()).id,
        )

        mock_user_show.assert_called_once_with(id=user["name"])
        updated = call_action("package_show", id=dataset["id"])
        assert tk.h.get_pkg_dict_extra(updated, "syndicated_id") is not None
