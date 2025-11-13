from __future__ import annotations

import dataclasses
import enum

import ckanapi

import ckan.plugins.toolkit as tk
from ckan.lib.jobs import DEFAULT_QUEUE_NAME

from ckanext.syndicate import config


class Topic(enum.Enum):
    create = enum.auto()
    update = enum.auto()
    unknown = enum.auto()


@dataclasses.dataclass
class Profile:
    id: str
    ckan_url: str = ""
    api_key: str = ""
    organization: str = ""
    flag: str = "syndicate"
    field_id: str = "syndicated_id"
    name_prefix: str = ""
    replicate_organization: bool = False
    update_organization: bool = False
    refresh_package_name: bool = False
    author: str = ""
    user_agent: str | None = None
    upload_organization_image: bool = True
    queue: str = DEFAULT_QUEUE_NAME

    def __post_init__(self):
        flags = [
            "replicate_organization",
            "update_organization",
            "upload_organization_image",
        ]

        for flag in flags:
            value = getattr(self, flag)
            if not isinstance(value, bool):
                setattr(self, flag, tk.asbool(value))

    def get_target(self):
        ckan = ckanapi.RemoteCKAN(self.ckan_url, apikey=self.api_key)
        if self.user_agent is not None:
            ckan.user_agent = self.user_agent
        return ckan
