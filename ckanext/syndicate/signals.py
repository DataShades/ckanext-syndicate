try:
    import ckan.plugins.toolkit as tk

    ckanext = tk.signals.ckanext
except AttributeError:
    from blinker import Namespace

    ckanext = Namespace()

before_syndication = ckanext.signal(u"syndicate:before_syndication")
"""Sent before package syndication happens.
Params:
    sender: local package ID
    profile: syndication profile
    details: data that will be sent to the remote portal
"""

after_syndication = ckanext.signal(u"syndicate:after_syndication")
"""Sent right after package syndication.
Params:
    sender: local package ID
    profile: syndication profile
    details: remote package details
"""

before_group_syndication = ckanext.signal(
    u"syndicate:before_group_syndication"
)
"""Sent before group/organization syndication happens.
Params:
    sender: local group ID
    profile: syndication profile
    details: data that will be sent to the remote portal
"""

after_group_syndication = ckanext.signal(u"syndicate:after_group_syndication")
"""Sent right after group/organization syndication.
Params:
    sender: local group ID
    profile: syndication profile
    remote: remote group details
"""
