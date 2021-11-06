RavenDB cluster node role
=========

Installs RavenDB server on a remote machine.

Requirements
------------

Debian or Red Hat based OS.

Role Variables
--------------

```
ravendb_version: latest

ravendb_version_minor: 5.2
ravendb_release_channel: stable

ravendb_settings_preset: local_setup
```

Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: ravendb_cluster
      roles:
         - { role: gregolsky.ravendb.ravendb-node, ravendb_version: 5.2.2 }

