import ckanapi
import factory
import pytest
from pytest_factoryboy import register

from ckan.tests import factories

from ckanext.syndicate.types import Profile


@pytest.fixture
def clean_db(reset_db, migrate_db_for):
    reset_db()

    migrate_db_for("syndicate")


@pytest.fixture
def ckan(sysadmin, app, monkeypatch):
    ckan = ckanapi.TestAppCKAN(app, sysadmin["token"])
    monkeypatch.setattr(Profile, "get_target", lambda *args: ckan)
    return ckan


class PackageFactory(factories.Dataset):
    owner_org = factory.LazyFunction(lambda: OrganizationFactory()["id"])


class PackageWithFlagFactory(factories.Dataset):
    extras = [{"key": "syndicate", "value": "true"}]


class UserFactory(factories.UserWithToken):
    pass


class SysadminFactory(factories.SysadminWithToken):
    pass


class GroupFactory(factories.Group):
    pass


class OrganizationFactory(factories.Organization):
    image_url = ""


register(OrganizationFactory, "organization")
register(UserFactory, "user")
register(GroupFactory, "group")
register(PackageFactory, "package")
register(SysadminFactory, "sysadmin")
register(PackageWithFlagFactory, "package_with_flag")
