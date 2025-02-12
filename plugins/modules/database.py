from ansible.module_utils.basic import AnsibleModule
from ravendb import DocumentStore, GetDatabaseNamesOperation
from ravendb.serverwide.operations.common import CreateDatabaseOperation, DeleteDatabaseOperation
from ravendb.serverwide.database_record import DatabaseRecord
from ravendb.exceptions.raven_exceptions import RavenException
import sys

def create_store(url, secure, certificate_path, ca_cert_path):
    store = DocumentStore(urls=[url])
    if secure and certificate_path:
        store.certificate_pem_path = certificate_path
        store.trust_store_path = ca_cert_path
    store.initialize()
    return store


def get_existing_databases(store):
    return store.maintenance.server.send(GetDatabaseNamesOperation(0, 128))


def handle_present_state(store, database_name, replication_factor, check_mode):
    existing_databases = get_existing_databases(store)

    if database_name in existing_databases:
        return False, f"Database '{database_name}' already exists."

    if check_mode:
        return True, f"Database '{database_name}' would be created."

    database_record = DatabaseRecord(database_name)
    create_database_operation = CreateDatabaseOperation(
        database_record=database_record,
        replication_factor=replication_factor
    )
    store.maintenance.server.send(create_database_operation)
    return True, f"Database '{database_name}' created successfully."


def handle_absent_state(store, database_name, check_mode):
    existing_databases = get_existing_databases(store)

    if database_name not in existing_databases:
        return False, f"Database '{database_name}' does not exist."

    if check_mode:
        return True, f"Database '{database_name}' would be deleted."

    delete_database_operation = DeleteDatabaseOperation(database_name)
    store.maintenance.server.send(delete_database_operation)
    return True, f"Database '{database_name}' deleted successfully."
   

def main():
    module_args = dict(
        url=dict(type='str', required=True),
        database_name=dict(type='str', required=True),
        replication_factor=dict(type='int', default=1),
        secure=dict(type='bool', default=False),
        certificate_path=dict(type='str', required=False),
        ca_cert_path=dict(type='str', required=False),
        state=dict(type='str', choices=['present', 'absent'], default='present')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    url = module.params['url']
    database_name = module.params['database_name']
    replication_factor = module.params['replication_factor']
    secure = module.params['secure']
    certificate_path = module.params.get('certificate_path')
    ca_cert_path = module.params.get('ca_cert_path')
    desired_state = module.params['state']

    try:
        store = create_store(url, secure, certificate_path, ca_cert_path)
        check_mode = module.check_mode

        if desired_state == 'present':
            changed, message = handle_present_state(store, database_name, replication_factor, check_mode)
        elif desired_state == 'absent':
            changed, message = handle_absent_state(store, database_name, check_mode)

        module.exit_json(changed=changed, msg=message)

    except RavenException as e:
        module.fail_json(msg=f"RavenDB operation failed: {str(e)}")
    except Exception as e:
        module.fail_json(msg=f"An unexpected error occurred: {str(e)}")
    finally:
        if 'store' in locals():
            store.close()


if __name__ == '__main__':
    main()
