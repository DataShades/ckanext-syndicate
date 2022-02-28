# -*- coding: utf-8 -*-
from __future__ import annotations
from collections import Counter

import logging
import time

import ckan.model as model
import ckan.plugins.toolkit as tk
import click

import ckanext.syndicate.utils as utils


def get_commands():
    return [syndicate]


@click.group()
def syndicate():
    pass


@syndicate.command()
@click.argument("id", required=False)
@click.option("-t", "--timeout", type=float, default=0)
@click.option("-f", "--foreground", is_flag=True)
def sync(id, timeout, foreground):
    """Syndicate datasets to remote portals."""

    packages = model.Session.query(model.Package)
    if id:
        packages = packages.filter(
            (model.Package.id == id) | (model.Package.name == id)
        )

    total = packages.count()

    with click.progressbar(packages, length=total) as bar:
        for package in bar:
            bar.label = "Sending syndication signal to package {}".format(
                package.id
            )
            utils.try_sync(package.id)
            time.sleep(timeout)


@syndicate.command()
def init():
    """Creates new syndication table."""
    tk.error_shout(
        "`ckan syndicate init` is not required and takes no effect anymore"
    )


@syndicate.command()
@click.argument("ids", nargs=-1)
def check(ids: tuple[str]):
    """Print profiles that will be used in case of syndication of pagkage."""
    q = model.Session.query(model.Package)
    if ids:
        q = q.filter(model.Package.id.in_(ids) | model.Package.name.in_(ids))

    counter = Counter()
    for pkg in q:
        profiles = utils.profiles_for(pkg)

        names = [p.id for p in profiles]
        click.echo(f"{pkg.id}: {names}")

        for n in names:
            counter[n] += 1

    if not counter:
        return

    click.secho("Statistics:", bold=True)
    for profile, count in counter.items():
        click.secho(f"\t{profile}: {count}")
