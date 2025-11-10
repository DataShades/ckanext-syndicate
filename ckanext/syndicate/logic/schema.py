from __future__ import annotations

import ckan.plugins.toolkit as tk
from ckan import types
from ckan.logic.schema import validator_args

from ckanext.syndicate import utils
from ckanext.syndicate.types import Profile, Topic


def into_topic(value: str) -> Topic:
    return Topic[value]


def into_profile(value: str) -> Profile:
    profile = utils.get_profile(value)
    if not profile:
        raise tk.Invalid(f"Profile {value} does not exist")
    return profile


@validator_args
def syndicate_sync(
    not_missing: types.Validator,
    one_of: types.ValidatorFactory,
    unicode_safe: types.Validator,
    package_id_or_name_exists: types.Validator,
) -> types.Schema:
    return {
        "id": [not_missing, package_id_or_name_exists],
        "topic": [not_missing, one_of(["create", "update"]), into_topic],
        "profile": [not_missing, unicode_safe, into_profile],
    }


@validator_args
def syndicate_prepare() -> types.Schema:
    return syndicate_sync()


@validator_args
def sync_organization(
    not_missing: types.Validator,
    unicode_safe: types.Validator,
    group_id_or_name_exists: types.Validator,
    default: types.ValidatorFactory,
    boolean_validator: types.Validator,
) -> types.Schema:
    return {
        "id": [not_missing, group_id_or_name_exists],
        "profile": [not_missing, unicode_safe, into_profile],
        "update_existing": [default(False), boolean_validator],
    }


sync_group = sync_organization
