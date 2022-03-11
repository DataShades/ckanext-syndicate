from __future__ import annotations


def get_auth_functions():
    return {
        "syndicate_sync": sync,
        "syndicate_prepare": prepare,
        "syndicate_sync_organization": sync_organization,
        "syndicate_sync_group": sync_group,
    }


def sync(context, data_dict):
    return {"success": False}


def prepare(context, data_dict):
    return {"success": False}


def sync_organization(context, data_dict):
    return {"success": False}


def sync_group(context, data_dict):
    return {"success": False}
