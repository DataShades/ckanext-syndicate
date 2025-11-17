from __future__ import annotations

import ckan.plugins.toolkit as tk

import ckanext.tables.shared as t

from ckanext.syndicate import model, utils


class ApiKeyFormatter(t.formatters.BaseFormatter):
    def format(self, value: t.Value, options: t.Options) -> t.FormatterResult:
        if not value:
            return tk.literal(f'<span class="text-uppercase badge text-bg-danger">{tk._("No API Key Set")}</span>')

        return tk.literal(f"<code>{value[:4]}************{value[-4:]}</code>")


class DetailsDialogModalFormatter(t.formatters.BaseFormatter):
    """Formatter to show log details in a modal dialog."""

    def format(self, value: t.Value, options: t.Options) -> t.FormatterResult:
        formatter = t.formatters.DialogModalFormatter(self.column, self.row, self.initial_row, self.table)

        options.update({"template": "syndicate/formatters/extras_modal.html"})

        return formatter.format(value, options)


class RemotePortalURLFormatter(t.formatters.BaseFormatter):
    def format(self, value: t.Value, options: t.Options) -> t.FormatterResult:
        if value == "-":
            return value

        profile = utils.get_profile(options["profile_id"])

        if not profile:
            return value

        remote_portal_url = f"{profile.ckan_url.rstrip('/')}/dataset/{value}"

        return tk.literal(f"<a href='{remote_portal_url}' target='_blank'>{value}</a>")


class LocalPortalURLFormatter(t.formatters.BaseFormatter):
    def format(self, value: t.Value, options: t.Options) -> t.FormatterResult:
        if not value:
            return ""

        local_portal_url = tk.url_for("dataset.read", id=value)

        return tk.literal(f"<a href='{local_portal_url}' target='_blank'>{value}</a>")


class StateFormatter(t.formatters.BaseFormatter):
    def format(self, value: t.Value, options: t.Options) -> t.FormatterResult:
        """Format the status value."""
        state_map = {
            model.SyndicationLog.State.SYNCED: "success",
            model.SyndicationLog.State.FAILED: "danger",
            model.SyndicationLog.State.STOPPED: "black",
        }

        label_type = state_map.get(value, "black")

        return tk.literal(f'<span class="text-uppercase px-2 py-1 badge bg-{label_type}">{value}</span>')
