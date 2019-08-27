import logging
from time import sleep
from itertools import izip_longest as zip_longest

import ckan.model as ckan_model
import ckan.plugins.toolkit as tk
import paste.script
from ckan.lib.cli import CkanCommand
from ckan.plugins import get_plugin

import ckanext.syndicate.syndicate_model.model as model
from ckanext.syndicate.syndicate_model.syndicate_config import SyndicateConfig

log = logging.getLogger('ckanext.syndicate')


class SyndicateCommand(CkanCommand):
    """
    Ckanext-syndicate management commands.

    Usage::
        paster syndicate [command]
    """

    summary = __doc__.split('\n')[0]
    usage = __doc__

    parser = paste.script.command.Command.standard_parser(verbose=True)
    parser.add_option(
        '-c',
        '--config',
        dest='config',
        default='development.ini',
        help='Config file to use.'
    )

    def command(self):
        self._load_config()

        if not len(self.args):
            print self.usage
        elif self.args[0] == 'init':
            self._init()
        elif self.args[0] == 'drop':
            self._drop()
        elif self.args[0] == 'create':
            self._create()
        elif self.args[0] == 'sync':
            self._sync()

    def _init(self):
        self._drop()
        self._create()
        self._seed()
        log.info("DB tables are reinitialized")

    def _drop(self):
        model.drop_tables()
        log.info("DB tables are removed")

    def _create(self):
        model.create_tables()
        log.info("DB tables are setup")

    def _seed(self):
        options = self.read_vars(self.options.config, 'app:main')
        prefix = 'ckan.syndicate.'
        keys = (
            'ckan_url', 'api_key', 'organization', 'replicate_organization',
            'author', 'predicate', 'field_id', 'flag', 'prefix'
        )
        profile_lists = zip_longest(
            *map(lambda key: tk.aslist(options.get(prefix + key)), keys)
        )
        for item in profile_lists:
            profile = SyndicateConfig._for_seed(item)
            ckan_model.Session.add(profile)
            print('Added profile: {}'.format(profile))
        ckan_model.Session.commit()

    def _sync(self):
        plugin = get_plugin('syndicate')
        from ckanext.syndicate.plugin import get_syndicate_flag

        packages = ckan_model.Session.query(ckan_model.Package
                                            ).filter_by(state='active')
        if len(self.args) > 1:
            packages = [ckan_model.Package.get(self.args[1])]

        for package in packages:
            sleep(1)
            package.extras[get_syndicate_flag()] = 'true'
            print('Sending syndication signal to {}'.format(package.id))
            plugin.notify(package, 'changed')
