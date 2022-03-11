import ckan.model as model
import ckan.plugins as p
import pytest
from ckan.model.domain_object import DomainObjectOperation

from ckanext.syndicate.types import Topic


@pytest.fixture
def plugin():
    yield p.get_plugin("syndicate")


@pytest.fixture
def dataset(package):
    yield model.Package.get(package["id"])


@pytest.fixture
def dataset_with_flag(dataset):
    dataset.extras = {"syndicate": "True"}
    yield dataset


@pytest.fixture
def syndicate(mocker):
    yield mocker.patch("ckanext.syndicate.utils.syndicate_dataset")


@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestDatasetNotify:
    def test_syndicates_task_for_create(
        self, syndicate, plugin, dataset_with_flag, mocker
    ):
        plugin.notify(dataset_with_flag, DomainObjectOperation.new)
        syndicate.assert_called_with(
            dataset_with_flag.id, Topic.create, mocker.ANY
        )

    def test_does_not_syndicate_for_private_dataset(
        self, syndicate, plugin, dataset_with_flag
    ):
        dataset_with_flag.private = True

        plugin.notify(dataset_with_flag, DomainObjectOperation.new)
        assert not (syndicate.called)

    def test_syndicates_task_for_update(
        self, syndicate, plugin, dataset_with_flag, mocker
    ):
        plugin.notify(dataset_with_flag, DomainObjectOperation.changed)
        syndicate.assert_called_with(
            dataset_with_flag.id, Topic.update, mocker.ANY
        )

    def test_does_not_syndicate_for_delete(
        self, syndicate, plugin, dataset_with_flag
    ):

        plugin.notify(dataset_with_flag, DomainObjectOperation.deleted)
        assert not (syndicate.called)


@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestSyndicateFlag:
    def test_syndicate_flag_with_capital_t(
        self, syndicate, plugin, dataset, mocker
    ):

        dataset.extras = {"syndicate": "True"}
        plugin.notify(dataset, DomainObjectOperation.new)
        syndicate.assert_called_with(dataset.id, Topic.create, mocker.ANY)

    def test_not_syndicated_when_flag_false(self, syndicate, plugin, dataset):
        dataset.extras = {"syndicate": "false"}

        plugin.notify(dataset, DomainObjectOperation.new)
        assert not (syndicate.called)

    def test_not_syndicated_when_flag_missing(
        self, syndicate, plugin, dataset
    ):
        plugin.notify(dataset, DomainObjectOperation.new)
        assert not (syndicate.called)


@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestPrepareFromPlugin:
    @pytest.mark.ckan_config("ckan.plugins", "test_syndicate syndicate")
    def test_pepare_called_if_first(self, plugin, dataset, mocker, syndicate):
        impl = p.get_plugin("test_syndicate")
        spy = mocker.spy(impl, "skip_syndication")
        plugin.notify(dataset, DomainObjectOperation.changed)
        spy.assert_called_once()
        syndicate.assert_called_once()

    @pytest.mark.ckan_config("ckan.plugins", "test_syndicate syndicate")
    @pytest.mark.ckan_config("ckanext.test_syndicate.skip_syndication", True)
    def test_pepare_from_plugin_has_effect(self, plugin, dataset, syndicate):
        plugin.notify(dataset, DomainObjectOperation.changed)
        syndicate.assert_not_called()

    @pytest.mark.ckan_config("ckan.plugins", "syndicate test_syndicate")
    def test_pepare_not_called_if_second(self, plugin, dataset, mocker):
        impl = p.get_plugin("test_syndicate")
        spy = mocker.spy(impl, "skip_syndication")
        plugin.notify(dataset, DomainObjectOperation.changed)
        spy.assert_not_called()
