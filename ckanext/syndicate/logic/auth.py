from __future__ import annotations

from ckan import types


def syndicate_sync(context: types.Context, data_dict: types.DataDict):
    return {"success": False}


def syndicate_prepare(context: types.Context, data_dict: types.DataDict):
    return {"success": False}


def syndicate_sync_organization(context: types.Context, data_dict: types.DataDict):
    return {"success": False}


def syndicate_sync_group(context: types.Context, data_dict: types.DataDict):
    return {"success": False}
