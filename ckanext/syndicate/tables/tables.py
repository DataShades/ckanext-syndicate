from __future__ import annotations

import ckan.plugins.toolkit as tk

import ckanext.tables.shared as t

from ckanext.syndicate import utils
from ckanext.syndicate.tables.data_sources import ProfilesDataSource
from ckanext.syndicate.tables.formatters import (
    ApiKeyFormatter,
    ExtrasDialogModalFormatter,
)


class DashboardTable(t.TableDefinition):
    def __init__(self):
        super().__init__(
            name="logs",
            data_source=ProfilesDataSource(),  # type: ignore
            columns=[
                t.ColumnDefinition(field="id", title="Profile", resizable=False),
                t.ColumnDefinition(
                    field="ckan_url",
                    title="CKAN URL",
                    resizable=False,
                    formatters=[(t.formatters.URLFormatter, {})],
                    tabulator_formatter="html",
                ),
                t.ColumnDefinition(
                    field="api_key",
                    title="API Key",
                    formatters=[(ApiKeyFormatter, {})],
                    tabulator_formatter="html",
                    width=160,
                ),
                t.ColumnDefinition(field="organization"),
                t.ColumnDefinition(field="author"),
                t.ColumnDefinition(
                    field="details",
                    title="",
                    formatters=[(ExtrasDialogModalFormatter, {})],
                    tabulator_formatter="html",
                    width=50,
                    resizable=False,
                    sortable=False,
                ),
            ],
            table_actions=[
                t.TableActionDefinition(
                    action="resyndicate_all",
                    label=tk._("Sync all profiles"),
                    callback=self.table_action_resyndicate_all,
                    icon="fa fa-sync",
                ),
            ],
            row_actions=[
                t.RowActionDefinition(
                    action="sync",
                    label=tk._("Sync"),
                    callback=self.row_action_sync_profile,
                    icon="fa fa-sync",
                    with_confirmation=True,
                ),
            ],
        )

    def table_action_resyndicate_all(self) -> t.ActionHandlerResult:
        for _ in utils.get_profiles():
            # TODO : the func is to be implemented
            # utils.syndicate_all_datasets(profile)
            pass

        return t.ActionHandlerResult(
            success=True,
            error=None,
            message=tk._("Resyndication jobs have been queued."),
        )

    def row_action_sync_profile(self, row: t.Row) -> t.ActionHandlerResult:
        profile = utils.get_profile(row["id"])

        if not profile:
            return t.ActionHandlerResult(
                success=False,
                error="not_found",
                message=tk._("Profile not found."),
            )

        # TODO: the func is to be implemented
        # utils.syndicate_profile(profile)

        return t.ActionHandlerResult(
            success=True,
            error=None,
            message=tk._("Resyndication job has been queued."),
        )
