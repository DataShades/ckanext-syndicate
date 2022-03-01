from __future__ import annotations

import enum
import dataclasses
from typing import Any

import ckan.plugins.toolkit as tk


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
    author: str = ""

    predicate: str = ""
    extras: dict[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.replicate_organization, bool):
            self.replicate_organization = tk.asbool(
                self.replicate_organization
            )
