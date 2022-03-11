from __future__ import annotations

import ckan.plugins.toolkit as tk
from ckan.logic.schema import validator_args

from .. import types, utils


def into_topic(value):
    return types.Topic[value]


def into_profile(value):
    profile = utils.get_profile(value)
    if not profile:
        raise tk.Invalid(f"Profile {value} does not exist")
    return profile


@validator_args
def sync(not_missing, one_of, unicode_safe, package_id_or_name_exists):
    return {
        "id": [not_missing, package_id_or_name_exists],
        "topic": [not_missing, one_of(["create", "update"]), into_topic],
        "profile": [not_missing, unicode_safe, into_profile],
    }


prepare = sync


@validator_args
def sync_organization(
    not_missing,
    unicode_safe,
    group_id_or_name_exists,
    default,
    boolean_validator,
):
    return {
        "id": [not_missing, group_id_or_name_exists],
        "profile": [not_missing, unicode_safe, into_profile],
        "skip_existing": [default(False), boolean_validator],
    }


sync_group = sync_organization
