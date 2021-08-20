RavenDB cluster node role
=========

Installs RavenDB server on a remote machine.

Requirements
------------

Debian or Red Hat based OS.

Role Variables
--------------

```
ravendb_server_version: latest

ravendb_server_version_minor: 5.2
ravendb_server_release_channel: stable

ravendb_run_unsecured: no
```

Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
