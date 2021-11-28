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

ravendb_settings_preset: local_setup (default: None)

# secure setup variables
ravendb_certificate_file: 
ravendb_certificate_password: 
ravendb_certificate_letsencrypt_email: 

# add/override settings
ravendb_settings_override:
```

Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: ravendb_cluster_nodes
      roles:
         - { role: gregolsky.ravendb.ravendb_node, ravendb_version: 5.2.2 }

