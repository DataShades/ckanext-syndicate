from __future__ import annotations

from dataclasses import asdict

import ckanext.tables.shared as t

from ckanext.syndicate import utils


class ProfilesDataSource(t.ListDataSource):
    def __init__(self):
        super().__init__(self._prepare_profiles())  # type: ignore

    def _prepare_profiles(self) -> list[dict[str, t.Value]]:
        return [
            {
                "id": profile.id,
                "ckan_url": profile.ckan_url,
                "api_key": profile.api_key,
                "organization": profile.organization,
                "author": profile.author,
                "details": self._clear_sensetive_data(asdict(profile)),
            }
            for profile in utils.get_profiles()
        ]

    def _clear_sensetive_data(self, data: dict[str, t.Value]) -> dict[str, t.Value]:
        if "api_key" in data:
            data["api_key"] = "************"

        return data
