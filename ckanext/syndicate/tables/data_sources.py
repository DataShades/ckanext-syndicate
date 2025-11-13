from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.engine.row import RowMapping

from ckan import model

import ckanext.tables.shared as t

from ckanext.syndicate import utils
from ckanext.syndicate.model import SyndicationLog


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
                "field_id": profile.field_id,
                "details": self._clear_sensetive_data(asdict(profile)),
            }
            for profile in utils.get_profiles()
        ]

    def _clear_sensetive_data(self, data: dict[str, t.Value]) -> dict[str, t.Value]:
        if "api_key" in data:
            data["api_key"] = f"****{data['api_key'][-4:]}"

        return data

class ProfileLogsDataSource(t.DatabaseDataSource):
    def __init__(self, profile_id: str):
        super().__init__(  # type: ignore
            stmt=select(
                SyndicationLog.local_id,
                SyndicationLog.target_id,
                SyndicationLog.state,
                SyndicationLog.error,
                SyndicationLog.timestamp,
                model.Package.id.label("pkg_id"),
                model.Package.title.label("pkg_title"),
                model.Package.name.label("pkg_name"),
            )
            .join(model.Package, SyndicationLog.local_id == model.Package.id)
            .filter(SyndicationLog.profile_id == profile_id)
            .order_by(SyndicationLog.timestamp.desc()),
            model=SyndicationLog,
        )

    def serialize_row(self, row: RowMapping) -> dict[str, Any]:
        data = dict(row)

        # Extra data for the formatters
        data["local_package"] = {
            "id": data.pop("pkg_id", None),
            "title": data.pop("pkg_title", None),
        }

        return data
