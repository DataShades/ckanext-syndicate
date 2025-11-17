from flask import Blueprint, Response

import ckan.plugins.toolkit as tk

import ckanext.tables.shared as t

from ckanext.syndicate.tables import DashboardTable, ProfileLogsTable

syndicate = Blueprint("syndicate", __name__, url_prefix="/ckan-admin/syndicate")


class ProfileLogsTableView(t.GenericTableView):
    def get(self, profile_id: str) -> str | Response:  # type: ignore
        if not self.check_access():
            return tk.abort(403, tk._("You are not authorized to view this table."))

        table = self.table(profile_id=profile_id)  # type: ignore
        self.breadcrumb_label = tk._("Profile Logs: %s") % profile_id

        return self._dispatch_get(table)

    def post(self, profile_id: str) -> Response:  # type: ignore
        if not self.check_access():
            return tk.abort(403, tk._("You are not authorized to perform this action."))

        table_instance = self.table(profile_id=profile_id)  # type: ignore

        return self._dispatch_post(table_instance)


syndicate.add_url_rule(
    "/dashboard",
    view_func=t.GenericTableView.as_view(
        "dashboard",
        table=DashboardTable,
        breadcrumb_label=tk._("Syndication Dashboard"),
    ),
)

syndicate.add_url_rule(
    "/profile/<profile_id>",
    view_func=ProfileLogsTableView.as_view("profile_logs", table=ProfileLogsTable),
)
