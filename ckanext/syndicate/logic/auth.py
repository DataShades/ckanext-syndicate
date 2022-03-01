from __future__ import annotations


def get_auth_functions():
    return {
        "syndicate_sync": sync,
        "syndicate_prepare": prepare,
    }


def sync(context, data_dict):
    return {"success": False}


def prepare(context, data_dict):
    return {"success": False}
