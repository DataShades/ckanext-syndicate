import ckanapi
import pytest
from pytest_factoryboy import register

from ckan.tests import factories

from ckanext.syndicate import utils


@pytest.fixture
def ckan(user, app, monkeypatch):
    ckan = ckanapi.TestAppCKAN(app, user["apikey"])
    monkeypatch.setattr(utils, "get_target", lambda *args: ckan)
    yield ckan


@register
class PackageFactory(factories.Dataset):
    pass


@register
class UserFactory(factories.User):
    pass


@register
class GroupFactory(factories.Group):
    pass


class OrganizationFactory(factories.Organization):
    pass


register(OrganizationFactory, "organization")
