from __future__ import annotations


def get_auth_functions():
    return {
        "syndicate_sync": sync,
    }


def sync(context, data_dict):
    return {"success": False}
