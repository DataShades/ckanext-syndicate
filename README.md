[![Tests](https://github.com/DataShades/ckanext-syndicate/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-syndicate/actions/workflows/test.yml)

# ckanext-syndicate

CKAN plugin for dataset syndication between CKAN instances

This plugin provides a mechanism for syndicating datasets to another CKAN instance. If a dataset has the `syndicate` flag set to `True` in its custom metadata, any updates to that dataset will be reflected in the syndicated version.

Resources in the syndicated dataset are stored as URLs pointing to the resources in the original dataset. You must have the **API key** of a user on the target CKAN instance. See the Config Settings section below for details.

Other plugins can modify the data being syndicated or react to before/after syndication events by implementing the ISyndicate interface and subscribing to the corresponding signals. This is useful when schemas differ between CKAN instances.

## Requirements

> Python 3.10+

> To work over SSL, requires `pyOpenSSL`

Compatibility with core CKAN versions:

| CKAN version    | Compatibility |
| --------------- | ------------- |
| 2.9 and earlier | no            |
| 2.10            | yes           |
| 2.11            | yes           |

## Installation

To install ckanext-auth:

1. Activate your CKAN virtual environment, for example:
```sh
. /usr/lib/ckan/default/bin/activate
```
2. Clone the source and install it on the virtualenv
```sh
git clone https://github.com/DataShades/ckanext-syndicate.git
cd ckanext-syndicate
pip install -e .
```
3. Add `syndicate tables` to the `ckan.plugins` setting in your CKAN config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Apply database migrations:
```
ckan db upgrade
```
5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:
```
sudo service apache2 reload
```

## Config settings

Syndication performs dataset creation and updates on the remote portal. It also
possible to syndicate the dataset to the multiple portals
simultaneously. ckanext-syndicate makes no assumptions as to how many
syndication endpoints you have and performs each synchronization separately as
if you've configured the first syndication endpoint, did syndication, updated
configuration did syndication once again.

Internally, set of config option related to the particular endpoint is called
profile(`ckanext.syndicate.types.Profile`). Each profile has an `ID`. `ID` is a
part of config option: `ckanext.syndicate.profile.<PROFILE ID>.<OPTION>` If
you want to syndicate dataset to the two different portals, `first` and
`another`, configuration may look like:

```ini
ckanext.syndicate.profile.first.ckan_url = https://data.example.com
ckanext.syndicate.profile.another.ckan_url = https://another.example.com
```

Here is the full list of config options available for `Profile`. Don't forget
to replace `PROFILE_ID` with any identifier you like.

> Note: In the options below, PREFIX = ckanext.syndicate.profile.PROFILE_ID.

| **Option**                                                         | **Default**     |**Example**                            | **Description**                                                                                                                                   |
| ------------------------------------------------------------------ | --------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------|
| `PREFIX.ckan_url`                    | *(required)*    | `https://data.example.com`            | The URL of the target CKAN instance to which datasets will be syndicated.                                                                         |
| `PREFIX.api_key`                     | *(required)*    | `9efdd954-c643-444a-97a1-c9c374cef861`| The API key of the user on the target CKAN instance.                                                                                              |
| `PREFIX.flag`                        | `syndicate`     | `syndicate_to_hdx`                    | The custom metadata flag used to mark datasets for syndication.                                                                                   |
| `PREFIX.field_id`                    | `syndicated_id` | `hdx_id`                              | The custom metadata field used to store the syndicated dataset ID on the original dataset.                                                        |
| `PREFIX.name_prefix`                 | `''`            | `my-prefix`                           | A prefix added to the name of the syndicated dataset.                                                                                             |
| `PREFIX.organization`                | `None`          | `test-org`                            | The name of the organization on the target CKAN instance where syndicated datasets are created.                                                   |
| `PREFIX.replicate_organization`      | `false`         | `true`                                | Whether to replicate the original dataset’s organization on the target CKAN instance.                                                             |
| `PREFIX.update_organization`         | `false`         | `true`                                | Whether to update organization metadata (doesn't update extras) if exists                                                                         |
| `PREFIX.author`                      | `None`          | `ricardomm`                           | The username whose API key is used. If a dataset already exists on the target CKAN, it will only be updated if its creator matches this username. |


In addition, the following config options control behavior of syndication process in general:

| **Option**                          | **Default** | **Description**                                                                                                                                              |
| ----------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ckanext.syndicate.sync_on_changes` | `true`      | Whether to automatically syndicate datasets whenever they are created, updated, or deleted. Disable this option if syndication should be triggered manually. |
| `ckanext.syndicate.queue.name`      | `default`   | The name of the background jobs queue used for syndication tasks.                                                                                            |


## Extending

### Signals

Syndication can be configured for each individual portal. There are two types of customization: reactions to events and changes to workflow.

Reactions are useful when you need to perform a side-effect right before or right after the syndication. This can be achieved via the [blinker's signals](https://pythonhosted.org/blinker/). The ckanext-syndicate provides two signals that can be imported from the [`ckanext.syndicate.signals`](./ckanext/syndicate/signals.py) (or subscribe via [ISignal](https://docs.ckan.org/en/latest/extensions/plugin-interfaces.html#ckan.plugins.interfaces.ISignal) starting from CKAN v2.10):

* `before_syndication`
* `after_syndication`
* `before_group_syndication`
* `after_group_syndication`

The `before_syndication` and `after_syndication` signals get the local dataset's ID as sender and extra keyword argument
with the name `profile` (current syndication profile). Basic subscription looks
like this:

```py
@after_syndication.connect
def after_syndication_listener(package_id, **kwargs):
    profile = kwargs.get("profile")
    if profile:
        do_something(package_id, profile)
```

### Interface

Changes to syndication workflow are made via `ckanext.syndicate.interfaces.ISyndicate` interface. At moment, it contains two methods:

* `skip_syndication` - decide, whether syndication must be performed for the
  given profile.
* `prepare_package_for_syndication` - update the package, before it sent to
  the remote portal. It can be really useful if the portal that you are
  syndicating to, is using a different metadata schema.
* `prepare_group_for_syndication` - update the group, before it sent to
  the remote portal.
* `reattach_on_syndication_error` - determines whether the local dataset should be reattached to an existing remote package when a syndication attempt fails due to the package already existing on the target CKAN instance.

Basic implementations look like this:

```py
class MyPlugin(plugins.Plugin):
    plugins.implements(ISyndicate, inherit=True)

    def skip_syndication(self, package: model.Package, profile: Profile) -> bool:
        if should_be_syndicated(package):
            return False
        return True

    def prepare_package_for_syndication(
        self, package_id: str, data_dict: dict[str, Any], profile: Profile
    ) -> dict[str, Any]:
        data_dict.pop("sensitive_field")
        return data_dict

    def prepare_group_for_syndication(
        self, group_id: str, group: dict[str, Any], profile: Profile
    ) -> dict[str, Any]:
        data_dict.pop("sensitive_field")
        return group

    def reattach_on_syndication_error(self, error: Exception) -> bool:
        if not isinstance(error, ckanapi.ValidationError):
            return False

        return "That URL is already in use." in error.error_dict.get("name", [])
```

Default implementation of `skip_syndication` prevents syndication for:

* private datasets
* datasets with the falsy value of the field, specified by `ckanext.syndicate.profile.PROFILE_ID.flag` config option (`syndicate` by default)

Default implementation of `reattach_on_syndication_error` returns `True` if the error is a `ckanapi.ValidationError` caused by an existing package with the same name on the target CKAN instance.

## CLI commands

Mass or individual syndication can be triggered as well from the command line:
```sh
ckan syndicate sync [ID]
```

Syndication provides that will be applied to the given datasets in case of syndication:
```sh
ckan syndicate check [ID]
```

## Tests

Install `dev-requirements.txt`:
```sh
pip install -r dev-requirements.txt
```

To run the tests, do:
```sh
pytest --ckan-ini=test.ini
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
