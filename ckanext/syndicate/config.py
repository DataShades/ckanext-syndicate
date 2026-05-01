import ckan.plugins.toolkit as tk

CONFIG_SYNC_ON_CHANGES = "ckanext.syndicate.sync_on_changes"
CONFIG_SYNC_ON_MEMBER_CHANGES = "ckanext.syndicate.sync_on_member_changes"


def get_sync_on_changes() -> bool:
    return tk.asbool(tk.config[CONFIG_SYNC_ON_CHANGES])


def get_sync_on_member_changes() -> bool:
    return tk.asbool(tk.config[CONFIG_SYNC_ON_MEMBER_CHANGES])
