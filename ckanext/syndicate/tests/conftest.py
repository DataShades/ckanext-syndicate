import ckanapi
import pytest
from pytest_factoryboy import register

from ckan.tests import factories

from ckanext.syndicate import types


@pytest.fixture
def ckan(user, api_token_factory, app, monkeypatch):
    token = api_token_factory(user=user["name"])
    ckan = ckanapi.TestAppCKAN(app, token["token"])
    monkeypatch.setattr(types.Profile, "get_target", lambda *args: ckan)
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
