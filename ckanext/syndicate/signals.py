try:
    import ckan.plugins.toolkit as tk

    ckanext = tk.signals.ckanext
except AttributeError:
    from blinker import Namespace

    ckanext = Namespace()

before_syndication = ckanext.signal("syndicate:before_syndication")
after_syndication = ckanext.signal("syndicate:after_syndication")

before_group_syndication = ckanext.signal("syndicate:before_group_syndication")
after_group_syndication = ckanext.signal("syndicate:after_group_syndication")
