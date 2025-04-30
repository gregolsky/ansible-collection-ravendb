# Changelog

All notable changes to this project will be documented in this file.

This project follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) principles and the [Ansible collection changelog format](https://docs.ansible.com/ansible/latest/dev_guide/collections_changelogs.html).

The full changelog is maintained in [changelogs/changelog.yml](./changelogs/changelog.yml).

## [1.0.0] - Initial Release

### Added
- Initial release of the `community.ravendb` Ansible Collection.
- Added `ravendb_node` role for setting up RavenDB servers.
- Added `ravendb_python_client_prerequisites` role for managing Python dependencies.
- Added modules:
  - `community.ravendb.database` for managing RavenDB databases.
  - `community.ravendb.index` for managing RavenDB indexes and index modes.
  - `community.ravendb.node` for adding nodes to a RavenDB cluster.