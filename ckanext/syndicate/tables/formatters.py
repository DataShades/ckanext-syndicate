from __future__ import annotations

import ckan.plugins.toolkit as tk

import ckanext.tables.shared as t


class ApiKeyFormatter(t.formatters.BaseFormatter):
    def format(self, value: t.Value, options: t.Options) -> t.FormatterResult:
        if not value:
            return tk.literal(f'<span class="text-uppercase badge text-bg-danger">{tk._("No API Key Set")}</span>')

        return tk.literal(f"<code>{value[:4]}************{value[-4:]}</code>")


class ExtrasDialogModalFormatter(t.formatters.BaseFormatter):
    """Formatter to show log details in a modal dialog."""

    def format(self, value: t.Value, options: t.Options) -> t.FormatterResult:
        formatter = t.formatters.DialogModalFormatter(self.column, self.row, self.initial_row, self.table)

        options.update({"template": "syndicate/formatters/extras_modal.html"})

        return formatter.format(value, options)
