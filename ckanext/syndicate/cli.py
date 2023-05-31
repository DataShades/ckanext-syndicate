# -*- coding: utf-8 -*-
from __future__ import annotations

import time
from collections import Counter

import click

import ckan.model as model
import ckan.plugins.toolkit as tk

from . import tasks, utils
from .types import Topic


def get_commands():
    return [syndicate]


@click.group()
def syndicate():
    pass


@syndicate.command()
@click.argument("id", required=False)
@click.option("-t", "--timeout", type=float, default=0)
@click.option("-f", "--foreground", is_flag=True)
@click.pass_context
def sync(ctx: click.Context, id, timeout, foreground):
    """Syndicate datasets to remote portals."""

    packages = model.Session.query(model.Package)
    if id:
        packages = packages.filter(
            (model.Package.id == id) | (model.Package.name == id)
        )

    total = packages.count()

    with ctx.meta["flask_app"].test_request_context():
        tk.g.syndication = True
        with click.progressbar(packages, length=total) as bar:
            for package in bar:
                bar.label = "Sending syndication signal to package {}".format(
                    package.id
                )
                for profile in utils.profiles_for(package):
                    if foreground:
                        tasks.sync_package(package.id, Topic.update, profile)
                    else:
                        utils.syndicate_dataset(package.id, Topic.update, profile)

                time.sleep(timeout)


@syndicate.command()
def init():
    """Creates new syndication table."""
    tk.error_shout("`ckan syndicate init` is not required and takes no effect anymore")


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
        if not names:
            continue

        counter.update(names)
        click.echo("{}: {}".format(pkg.id, ", ".join(names)))

    if not counter:
        return

    click.secho("Statistics:", bold=True)
    for profile, count in counter.items():
        click.secho(f"\t{profile}: {count}")
