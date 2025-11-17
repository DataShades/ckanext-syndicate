from __future__ import annotations

import ckan.plugins.toolkit as tk
from ckan import model

import ckanext.tables.shared as t

from ckanext.syndicate import utils
from ckanext.syndicate.tables.data_sources import (
    ProfileLogsDataSource,
    ProfilesDataSource,
)
from ckanext.syndicate.tables.formatters import (
    ApiKeyFormatter,
    DetailsDialogModalFormatter,
    LocalPortalURLFormatter,
    RemotePortalURLFormatter,
    StateFormatter,
)
from ckanext.syndicate.types import Topic


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
                t.ColumnDefinition(
                    field="details",
                    title="Details",
                    formatters=[(DetailsDialogModalFormatter, {})],
                    tabulator_formatter="html",
                    width=100,
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
                t.RowActionDefinition(
                    action="view_logs",
                    label=tk._("View logs"),
                    callback=lambda row: t.ActionHandlerResult(
                        success=True,
                        redirect=tk.url_for("syndicate.profile_logs", profile_id=row["id"]),
                    ),
                    icon="fa fa-list",
                ),
            ],
        )

    def table_action_resyndicate_all(self) -> t.ActionHandlerResult:
        for _ in utils.get_profiles():
            utils.sync_all_profiles()

        return t.ActionHandlerResult(
            success=True,
            error=None,
            message=tk._("Resyndication jobs have been queued."),
        )

    def row_action_sync_profile(self, row: t.Row) -> t.ActionHandlerResult:
        profile = utils.get_profile(row["id"])

        if not profile:
            return t.ActionHandlerResult(success=False, error=tk._("Profile not found."))

        utils.sync_profile(profile.id)

        return t.ActionHandlerResult(
            success=True,
            error=None,
            message=tk._("Profile sync job has been queued."),
        )


class ProfileLogsTable(t.TableDefinition):
    def __init__(self, profile_id: str):
        self.profile_id = profile_id

        super().__init__(
            name=f"syndication-profile-{profile_id}",
            data_source=ProfileLogsDataSource(profile_id),  # type: ignore
            table_template="syndicate/profile_logs_base.html",
            columns=[
                t.ColumnDefinition(
                    field="pkg_title",
                    title="Title",
                    sortable=False,
                    tooltip=True,
                ),
                t.ColumnDefinition(
                    field="local_id",
                    title="ID",
                    sortable=False,
                    formatters=[(LocalPortalURLFormatter, {"profile_id": profile_id})],
                    tabulator_formatter="html",
                    width=200,
                ),
                t.ColumnDefinition(
                    field="target_id",
                    title="Target Package ID",
                    sortable=False,
                    formatters=[(RemotePortalURLFormatter, {"profile_id": profile_id})],
                    tabulator_formatter="html",
                    width=200,
                ),
                t.ColumnDefinition(
                    field="state",
                    width=85,
                    resizable=False,
                    sortable=False,
                    formatters=[(StateFormatter, {})],
                    tabulator_formatter="html",
                ),
                t.ColumnDefinition(field="error", tooltip=True, sortable=False),
                t.ColumnDefinition(
                    field="timestamp",
                    title="Timestamp",
                    formatters=[(t.formatters.DateFormatter, {})],
                    width=155,
                    resizable=False,
                ),
            ],
            row_actions=[
                t.RowActionDefinition(
                    action="resyndicate_package",
                    label=tk._("Resyndicate Package"),
                    callback=self.row_action_resyndicate_package,
                    icon="fa fa-sync",
                    with_confirmation=True,
                ),
            ],
            bulk_actions=[
                t.BulkActionDefinition(
                    action="resyndicate_packages",
                    label=tk._("Resyndicate Packages"),
                    callback=self.bulk_action_resyndicate_package,
                    icon="fa fa-sync",
                ),
            ],
            exporters=t.ALL_EXPORTERS,
        )

    def row_action_resyndicate_package(self, row: t.Row) -> t.ActionHandlerResult:
        package = model.Package.get(row["pkg_id"])

        if package:
            # we call it to trigger a skip check
            pkg_profiles = utils.profiles_for(package)
            profile = next((p for p in pkg_profiles if p.id == self.profile_id), None)

            if profile:
                utils.sync_package(row["pkg_id"], Topic.update, profile)

        return t.ActionHandlerResult(
            success=True,
            error=None,
            message=tk._("Package has been resyndicated."),
        )

    def bulk_action_resyndicate_package(self, rows: list[t.Row]) -> t.ActionHandlerResult:
        for row in rows:
            package = model.Package.get(row["pkg_id"])

            if not package:
                continue

            # we call it to trigger a skip check
            pkg_profiles = utils.profiles_for(package)
            profile = next((p for p in pkg_profiles if p.id == self.profile_id), None)

            if profile:
                utils.syndicate_dataset(row["pkg_id"], Topic.update, profile)

        return t.ActionHandlerResult(
            success=True,
            error=None,
            message=tk._("Resyndication jobs have been queued."),
        )
