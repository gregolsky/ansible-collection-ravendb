import sys
import os
import re
from ansible.module_utils.basic import AnsibleModule
from ravendb import DocumentStore, AbstractIndexCreationTask
from ravendb.documents.indexes.abstract_index_creation_tasks import AbstractMultiMapIndexCreationTask
from ravendb.documents.operations.indexes import (
    GetIndexesOperation, DeleteIndexOperation, EnableIndexOperation, DisableIndexOperation, 
    StartIndexOperation, StopIndexOperation, GetIndexingStatusOperation, ResetIndexOperation)
from ravendb.documents.indexes.definitions import IndexRunningStatus
from ravendb.exceptions.raven_exceptions import RavenException
from urllib.parse import urlparse

def create_dynamic_index(name, definition):
    class DynamicIndex(AbstractIndexCreationTask):
        def __init__(self):
            super(DynamicIndex, self).__init__()
            self.map = definition.get("map")[0]
            reduce_def = definition.get("reduce")
            if reduce_def:
                self.reduce = reduce_def

    DynamicIndex.__name__ = name
    return DynamicIndex

def create_dynamic_multimap_index(name, definition):
    class DynamicIndex(AbstractMultiMapIndexCreationTask):
        def __init__(self):
            super(DynamicIndex, self).__init__()
            maps_def = definition.get("map")

            for map_def in maps_def:
                self._add_map(map_def)

            reduce_def = definition.get("reduce")
            if reduce_def:
                self.reduce = reduce_def

    DynamicIndex.__name__ = name
    return DynamicIndex

def initialize_ravendb_store(params):
    url = params['url']
    database_name = params['database_name']
    secure = params['secure']
    certificate_path = params.get('certificate_path')
    ca_cert_path = params.get('ca_cert_path')

    store = DocumentStore(urls=[url], database=database_name)
    if secure and certificate_path:
        store.certificate_pem_path = certificate_path
        store.trust_store_path = ca_cert_path

    store.initialize()
    return store

def reconcile_state(store, params, check_mode):
    database_name = params['database_name']
    index_name = params['index_name']
    desired_state = params.get('state')
    desired_mode = params.get('mode')
    cluster_wide = params['cluster_wide']

    database_maintenance = store.maintenance.for_database(database_name)
    existing_indexes = database_maintenance.send(GetIndexesOperation(0, sys.maxsize))
    existing_index_names = [i.name for i in existing_indexes]
   
    if desired_state == 'absent':
        return handle_absent_state(database_maintenance, index_name, existing_index_names, check_mode)

    if desired_state == 'present':
        return handle_present_state( store, database_name, params, index_name, existing_indexes, existing_index_names, check_mode)

    if desired_mode and desired_state is None:
        return handle_mode_only(store, index_name, desired_mode, cluster_wide, check_mode, existing_index_names)

    return "error", False, "Invalid state or mode combination."

def handle_absent_state(database_maintenance, index_name, existing_index_names, check_mode):
    if index_name not in existing_index_names:
        return "ok", False, f"Index '{index_name}' is already absent."

    if check_mode:
        return "ok", True, f"Index '{index_name}' would be deleted."

    database_maintenance.send(DeleteIndexOperation(index_name))
    return "ok", True, f"Index '{index_name}' deleted successfully."

def handle_present_state(store, database_name, params, index_name, existing_indexes, existing_index_names, check_mode):
    
    index_definition = params.get('index_definition')
    desired_mode = params.get('mode')
    cluster_wide = params['cluster_wide']

    if index_name in existing_index_names:
        existing_index = next(i for i in existing_indexes if i.name == index_name)
        if index_matches(existing_index, index_definition):
            if desired_mode:
                return apply_mode(store, index_name, desired_mode, cluster_wide, check_mode)
            return "ok", False, f"Index '{index_name}' already exists and matches definition."

    if check_mode:
        return "ok", True, f"Index '{index_name}' would be created."

    create_index(store, database_name, index_name, index_definition)
    if desired_mode:
        apply_mode(store, index_name, desired_mode, cluster_wide, check_mode)

    return "ok", True, f"Index '{index_name}' created successfully."


def handle_mode_only(store, index_name, desired_mode, cluster_wide, check_mode, existing_index_names):

    if index_name not in existing_index_names:
        return "error", False, f"Index '{index_name}' does not exist. Cannot apply mode."
    
    return apply_mode(store, index_name, desired_mode, cluster_wide, check_mode)



def create_index(store, database_name, index_name, index_definition):
    
    if len(index_definition.get("map")) > 1:
        DynamicIndexClass = create_dynamic_multimap_index(index_name, index_definition)
    else:
        DynamicIndexClass = create_dynamic_index(index_name, index_definition)
    index = DynamicIndexClass()
    index.execute(store, database_name)


def index_matches(existing_index, index_definition):
    
    existing_maps = set(map(str.strip, existing_index.maps)) if existing_index.maps else set()
    existing_reduce = getattr(existing_index, 'reduce', None)

    expected_maps = set(map(str.strip, index_definition.get("map", [])))
    normalized_existing_reduce = existing_reduce.strip() if existing_reduce else None
    normalized_expected_reduce = (index_definition.get("reduce") or "").strip()
    if not normalized_expected_reduce:
        normalized_expected_reduce = None

    return existing_maps == expected_maps and normalized_existing_reduce == normalized_expected_reduce


def enable_index(store, index_name, cluster_wide, check_mode):
    
    if check_mode:
        return "ok", True, f"Index '{index_name}' would be enabled {' cluster-wide' if cluster_wide else ''}."
    
    enable_index_operation = EnableIndexOperation(index_name, cluster_wide)
    store.maintenance.send(enable_index_operation)

    return "ok", True, f"Index '{index_name}' enabled successfully {' cluster-wide' if cluster_wide else ''}."

def disable_index(store, index_name, cluster_wide, check_mode):
        
    if check_mode:
        return "ok", True, f"Index '{index_name}' would be disabled {' cluster-wide' if cluster_wide else ''}."
    
    disable_index_operation = DisableIndexOperation(index_name, cluster_wide)
    store.maintenance.send(disable_index_operation)

    return "ok", True, f"Index '{index_name}' disbaled successfully {' cluster-wide' if cluster_wide else ''}."


def resume_index(store, index_name, check_mode):
        
    indexing_status = store.maintenance.send(GetIndexingStatusOperation())
    index = [x for x in indexing_status.indexes if x.name == index_name][0]
    if index.status == IndexRunningStatus.RUNNING:
        return "ok", False, f"Index '{index_name}' is already resumed and executing."

    if check_mode:
        return "ok", True, f"Index '{index_name}' would be resumed."
    
    resume_index_operation = StartIndexOperation(index_name)
    store.maintenance.send(resume_index_operation)

    return "ok", True, f"Index '{index_name}' resumed successfully."


def pause_index(store, index_name, check_mode):
    
    indexing_status = store.maintenance.send(GetIndexingStatusOperation())
    index = [x for x in indexing_status.indexes if x.name == index_name][0]
    if index.status == IndexRunningStatus.PAUSED:
        return "ok", False, f"Index '{index_name}' is already paused."

    if check_mode:
        return "ok", True, f"Index '{index_name}' would be paused."
    
    pause_index_operation = StopIndexOperation(index_name)
    store.maintenance.send(pause_index_operation)

    return "ok", True, f"Index '{index_name}' paused successfully."
	
def reset_index(store, index_name, check_mode):
    
    if check_mode:
        return "ok", True, f"Index '{index_name}' would be reset."
    
    reset_index_operation = ResetIndexOperation(index_name)
    store.maintenance.send(reset_index_operation)

    return "ok", True, f"Index '{index_name}' reset successfully."


def apply_mode(store, index_name, mode, cluster_wide, check_mode):
   
    match mode:
        case 'enabled':
            return enable_index(store, index_name, cluster_wide, check_mode)	
        case 'disabled':
            return disable_index(store, index_name, cluster_wide, check_mode)
        case 'resumed':
            return resume_index(store, index_name, check_mode)
        case 'paused':
            return pause_index(store, index_name, check_mode)
        case 'reset':
            return reset_index(store, index_name, check_mode)

def is_valid_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

def is_valid_name(name):
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))

def is_valid_dict(value):
    return isinstance(value, dict) or value is None

def is_valid_bool(value):
    return isinstance(value, bool)

def validate_paths(*paths):
    for path in paths:
        if path and not os.path.isfile(path):
            return False, f"Path does not exist: {path}"
    return True, None

def is_valid_state(state):
    return state in [None, 'present', 'absent']

def is_valid_mode(mode):
    return mode in [None, 'resumed', 'paused', 'enabled', 'disabled', 'reset']


def main():
    module_args = dict(
        url=dict(type='str', required=True),
        database_name=dict(type='str', required=True),
        index_name=dict(type='str', required=True),
        index_definition=dict(type='dict', required=False),
        secure=dict(type='bool', default=False),
        certificate_path=dict(type='str', required=False),
        ca_cert_path=dict(type='str', required=False),
        state=dict(type='str', choices=['present', 'absent'], required=False),
        mode=dict(type='str', choices=['resumed', 'paused', 'enabled', 'disabled', 'reset'], required=False),
        cluster_wide=dict(type='bool', default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    url = module.params['url']
    database_name = module.params['database_name']
    index_name = module.params['index_name']
    index_definition = module.params.get('index_definition')
    secure = module.params['secure']
    certificate_path = module.params.get('certificate_path')
    ca_cert_path = module.params.get('ca_cert_path')
    state = module.params.get('state')
    mode = module.params.get('mode')
    cluster_wide = module.params['cluster_wide']

    if not is_valid_url(url):
        module.fail_json(msg=f"Invalid URL: {url}")

    if not is_valid_name(database_name):
        module.fail_json(msg=f"Invalid database name: {database_name}. Only letters, numbers, dashes, and underscores are allowed.")

    if not is_valid_name(index_name):
        module.fail_json(msg=f"Invalid index name: {index_name}. Only letters, numbers, dashes, and underscores are allowed.")

    if not is_valid_dict(index_definition):
        module.fail_json(msg=f"Invalid index definition: Must be a dictionary.")

    if not is_valid_bool(secure):
        module.fail_json(msg=f"Invalid secure flag: {secure}. Must be a boolean.")

    valid, error_msg = validate_paths(certificate_path, ca_cert_path)
    if not valid:
        module.fail_json(msg=error_msg)

    if not is_valid_state(state):
        module.fail_json(msg=f"Invalid state: {state}. Must be 'present' or 'absent'.")

    if not is_valid_mode(mode):
        module.fail_json(msg=f"Invalid mode: {mode}. Must be one of 'resumed', 'paused', 'enabled', 'disabled', 'reset'.")

    if not is_valid_bool(cluster_wide):
        module.fail_json(msg=f"Invalid cluster_wide flag: {cluster_wide}. Must be a boolean.")

    try:
        store = initialize_ravendb_store(module.params)
        check_mode = module.check_mode

        type, changed, message = reconcile_state(store, module.params, check_mode)

        if type == "error":
            module.fail_json(changed=changed, msg=message)
        else:
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
