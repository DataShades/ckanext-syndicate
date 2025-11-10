import ckan.plugins.toolkit as tk

CONFIG_SYNC_ON_CHANGES = "ckanext.syndicate.sync_on_changes"
CONFIG_QUEUE_NAME = "ckanext.syndicate.queue.name"


def get_sync_on_changes() -> bool:
    return tk.asbool(tk.config[CONFIG_SYNC_ON_CHANGES])


def get_queue_name() -> str:
    return tk.config[CONFIG_QUEUE_NAME]
