import ckanapi
import pytest
from pytest_factoryboy import register

from ckan.tests import factories

from ckanext.syndicate.types import Profile


@pytest.fixture
def ckan(sysadmin, app, monkeypatch):
    ckan = ckanapi.TestAppCKAN(app, sysadmin["token"])
    monkeypatch.setattr(Profile, "get_target", lambda *args: ckan)
    return ckan


@register
class PackageFactory(factories.Dataset):
    pass


@register
class UserFactory(factories.UserWithToken):
    pass


class SysadminFactory(factories.SysadminWithToken):
    pass


@register
class GroupFactory(factories.Group):
    pass


class OrganizationFactory(factories.Organization):
    pass


register(OrganizationFactory, "organization")
register(SysadminFactory, "sysadmin")
