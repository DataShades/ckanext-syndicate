# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## [3.0.0](https://github.com/DataShades/ckanext-syndicate/compare/v2.2.2...v3.0.0) (2025-11-17)

### ⚠ BREAKING CHANGES

* Config options changes:
  * `ckan.plugins` now requires adding `tables` alongside `syndicate` for everything to work properly.
  * `ckanext.syndicate.profile.<PROFILE>.author` is dropped
  * `ckanext.syndicate.profile.<PROFILE>.queue` is added
  * `ckanext.syndicate.profile.<PROFILE>.field_id` is deprecated, but should remain for a database migration period.
  * `ckanext.syndicate.queue.name` dropped in favour of profile specific queue config
* Removed helpers:
  * `organization_owns_dataset`
  * `organization_not_owns_dataset`
* Removed interface methods:
  * `reattach_on_syndication_error`
* Deleted utils:
  * `try_sync`
  * `get_target`
  * `trigger_sync`
* Requirements updated:
  * Python >= 3.10
  * CKAN >= 2.10
* Previously deprecated actions removed:
  * `before_syndication_action`
  * `after_syndication_action`
  * `update_dataset_for_syndication`

### Features

* Add profile list dashboard and profile logs dashboard
* Add `SyndicationLog` model to track syndication attempts
* Refactored code, applied ruff fixess and removed redundant parts
* Dropped unused table `syndicate_config`
* Added config declaration for non-profile config options
* Improved test workflow
* Updated and rewrote README

### [2.2.2](https://github.com/DataShades/ckanext-syndicate/compare/v2.2.1...v2.2.2) (2023-05-31)


### Features

* configurable user agent ([afb2b7e](https://github.com/DataShades/ckanext-syndicate/commit/afb2b7e6d134b7ef13637696675f67349c8a8923))

### [2.2.1](https://github.com/DataShades/ckanext-syndicate/compare/v2.2.0...v2.2.1) (2023-05-26)


### Features

* prifile.refresh_package_name flag allows updating remote name ([db85496](https://github.com/DataShades/ckanext-syndicate/commit/db85496b90fa102ec6a750cc93fb07c6c0ccf0a4))

## [2.2.0](https://github.com/DataShades/ckanext-syndicate/compare/v2.1.1...v2.2.0) (2023-03-31)


### ⚠ BREAKING CHANGES

* existing group and organization are skipped by default(skip_existing->update_existing)

### Features

* existing group and organization are skipped by default(skip_existing->update_existing) ([d022e33](https://github.com/DataShades/ckanext-syndicate/commit/d022e33f65ec2319fb9571d8201b9e37fac1bded))

### [2.1.1](https://github.com/DataShades/ckanext-syndicate/compare/v2.1.0...v2.1.1) (2023-03-08)


### Bug Fixes

* 2.10 compatibility ([64a4ac4](https://github.com/DataShades/ckanext-syndicate/commit/64a4ac41e1e8ed0bc517c9af879ff029dcf17655))

## [2.1.0](https://github.com/DataShades/ckanext-syndicate/compare/v2.0.0...v2.1.0) (2023-02-02)


### Features

* optional upload of org image ([ee1ee8c](https://github.com/DataShades/ckanext-syndicate/commit/ee1ee8c9cd153a719ad73b6a7c992cf2f73064b7))
