from __future__ import annotations

from flask import Blueprint

import ckan.plugins.toolkit as tk

from ckanext.tables.shared import GenericTableView

from ckanext.syndicate.tables import DashboardTable

syndicate = Blueprint("syndicate", __name__, url_prefix="/ckan-admin/syndicate")

syndicate.add_url_rule(
    "/dashboard",
    view_func=GenericTableView.as_view(
        "dashboard",
        table=DashboardTable,
        breadcrumb_label=tk._("Syndication Dashboard"),
    ),
)
