import sys
from ravendb_test_driver import RavenTestDriver
from unittest import TestCase
from ansible_collections.ravendb.community.plugins.modules.index import *
from ravendb.documents.operations.indexes import GetIndexesOperation


INDEX_DEFINITION = {
        "map": [
            "from c in docs.Users select new { Name = c.name, UserCount = 1, OrderCount = 0, TotalCount = 1 }"]
    }

UPDATED_INDEX_DEFINITION = {
        "map": [
            "from c in docs.Users select new { Name = c.name, UserCount = 1, OrderCount = 0, TotalCount = 3 }"]
    }

MAP_REDUCE_INDEX_DEFINITION = {
        "map": [
            "from c in docs.Users select new { Name = c.name, UserCount = 1, OrderCount = 0, TotalCount = 1 }"],      
        "reduce": """
                from result in results
                group result by result.Name
                into g
                select new 
                { 
                Name = g.Key, 
                UserCount = g.Sum(x => x.UserCount),
                OrderCount = g.Sum(x => x.OrderCount),
                TotalCount = g.Sum(x => x.TotalCount)
                }
            """   
        
}

MULTI_MAP_INDEX_DEFINITION ={
    "map": ["from c in docs.Users select new { Name = c.name, UserCount = 1, OrderCount = 0, TotalCount = 1 }",
            "from o in docs.Orders select new { Name = o.customer, UserCount = 0, OrderCount = 1, TotalCount = 1 }"
           ]   
}

class TestReconcileState(TestCase):

    index_name = "test/index"

    def setUp(self):
      super().setUp()
      self.test_driver = RavenTestDriver()

    def test_create_index(self):
        store = self.test_driver.get_document_store(database="test_create_index")

        params = {
            "database_name": store.database,
            "index_name": "test_index",
            "index_definition": INDEX_DEFINITION,
            "state": "present",
            "cluster_wide": False,
        }

        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test_index' created successfully.", message)

    def test_create_already_exists_index(self):
        store = self.test_driver.get_document_store(database="test_create_already_exists_index")

        params = {
            "database_name": store.database,
            "index_name": "myindex",
            "index_definition": INDEX_DEFINITION,
            "state": "present",
            "cluster_wide": False,
        }

        _, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertTrue(changed)
        self.assertIn("Index 'myindex' created successfully.", message)

      # self.test_driver.wait_for_user_to_continue_the_test(store)
        
        _, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertFalse(changed)
        self.assertIn("Index 'myindex' already exists and matches definition.", message)
      

    def test_update_existing_index_with_modified_map(self):
        store = self.test_driver.get_document_store(database="test_update_existing_index_with_modified_map")

        params = {
            "database_name": store.database,
            "index_name": "test/index",
            "index_definition": INDEX_DEFINITION,
            "state": "present",
            "cluster_wide": False,
        }

        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test/index' created successfully.", message)

        params["index_definition"]=UPDATED_INDEX_DEFINITION
        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test/index' created successfully.", message)

        database_maintenance = store.maintenance.for_database(store.database)
        existing_indexes = database_maintenance.send(GetIndexesOperation(0, sys.maxsize))
        index = existing_indexes[0]

        existing_maps = list(map(str.strip, index.maps)) if index.maps else []
        expected_map_definition = UPDATED_INDEX_DEFINITION["map"]

        self.assertEqual(existing_maps[0], expected_map_definition[0])

    def test_update_existing_map_index_into_multi_map_index(self):
        store = self.test_driver.get_document_store(database="test_update_existing_map_index_into_multi_map_index")

        params = {
            "database_name": store.database,
            "index_name": "test/index",
            "index_definition": INDEX_DEFINITION,
            "state": "present",
            "cluster_wide": False,
        }

        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test/index' created successfully.", message)

        params["index_definition"]=MULTI_MAP_INDEX_DEFINITION
        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test/index' created successfully.", message)

        database_maintenance = store.maintenance.for_database(store.database)
        existing_indexes = database_maintenance.send(GetIndexesOperation(0, sys.maxsize))
        index = existing_indexes[0]

        existing_maps = sorted(list(map(str.strip, index.maps)) if index.maps else [])
        expected_map_definition = sorted(MULTI_MAP_INDEX_DEFINITION["map"])
     
        self.assertEqual(existing_maps[0], expected_map_definition[0])
        self.assertEqual(existing_maps[1], expected_map_definition[1])


    def test_update_existing_map_index_into_map_reduce_index(self):
        store = self.test_driver.get_document_store(database="test_update_existing_map_index_into_map_reduce_index")

        params = {
            "database_name": store.database,
            "index_name": "test/index",
            "index_definition": INDEX_DEFINITION,
            "state": "present",
            "cluster_wide": False,
        }

        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test/index' created successfully.", message)

        params["index_definition"]=MAP_REDUCE_INDEX_DEFINITION
        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test/index' created successfully.", message)

        database_maintenance = store.maintenance.for_database(store.database)
        existing_indexes = database_maintenance.send(GetIndexesOperation(0, sys.maxsize))
        index = existing_indexes[0]

        existing_maps = list(map(str.strip, index.maps)) if index.maps else []
        existing_reduce = getattr(index, 'reduce', None)

        expected_map_definition = MAP_REDUCE_INDEX_DEFINITION["map"]
        expected_redcue_definition=MAP_REDUCE_INDEX_DEFINITION["reduce"]

        self.assertEqual(existing_maps[0], expected_map_definition[0])
        self.assertEqual(existing_reduce, expected_redcue_definition)

    def test_delete_index(self):
        store = self.test_driver.get_document_store(database="test_delete_index")

        params = {
            "database_name": store.database,
            "index_name": self.index_name,
            "index_definition": INDEX_DEFINITION,
            "state": "present",
            "cluster_wide": False,
        }

        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test/index' created successfully.", message)

        params["state"]="absent"
        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertTrue(changed)
        self.assertIn("Index 'test/index' deleted successfully.", message)

    def test_delete_nonexistent_index (self):
        store = self.test_driver.get_document_store(database="test_delete_nonexistent_index")

        params = {
            "database_name": store.database,
            "index_name": self.index_name,
            "index_definition": INDEX_DEFINITION,
            "state": "present",
            "cluster_wide": False,
        }

        params["state"]="absent"
        status, changed, message = reconcile_state(store, params, check_mode=False)
        self.assertEqual(status, "ok")
        self.assertFalse(changed)
        self.assertIn("Index 'test/index' is already absent.", message)


class TestValidationFunctions(TestCase):
    
    def test_valid_url(self):
        self.assertTrue(is_valid_url("https://example.com"))
        self.assertTrue(is_valid_url("http://localhost:8080"))
        self.assertFalse(is_valid_url("example.com"))
        self.assertFalse(is_valid_url("://invalid-url"))

    def test_valid_database_name(self):
        self.assertTrue(is_valid_name("valid_db"))
        self.assertTrue(is_valid_name("Valid-DB-123"))
        self.assertFalse(is_valid_name("Invalid DB!"))
        self.assertFalse(is_valid_name(""))

    def test_valid_index_name(self):
        self.assertTrue(is_valid_name("valid_index"))
        self.assertTrue(is_valid_name("Index-123"))
        self.assertFalse(is_valid_name("Invalid Index!"))
        self.assertFalse(is_valid_name(""))

    def test_valid_index_definition(self):
        self.assertTrue(is_valid_dict({"field": "value"}))
        self.assertTrue(is_valid_dict(None))
        self.assertFalse(is_valid_dict("not a dict"))
        self.assertFalse(is_valid_dict(["list"]))

    def test_valid_certificate_paths(self):
        with open("test_cert.pem", "w") as f:
            f.write("dummy certificate content")
        with open("test_ca.pem", "w") as f:
            f.write("dummy CA content")

        self.assertEqual(validate_paths("test_cert.pem", "test_ca.pem"), (True, None))
        self.assertEqual(validate_paths("non_existing.pem"), (False, "Path does not exist: non_existing.pem"))

        os.remove("test_cert.pem")
        os.remove("test_ca.pem")

    def test_valid_state(self):
        self.assertTrue(is_valid_state("present"))
        self.assertTrue(is_valid_state("absent"))
        self.assertTrue(is_valid_state(None))
        self.assertFalse(is_valid_state("running"))

    def test_valid_mode(self):
        self.assertTrue(is_valid_mode("resumed"))
        self.assertTrue(is_valid_mode("paused"))
        self.assertTrue(is_valid_mode("enabled"))
        self.assertTrue(is_valid_mode("disabled"))
        self.assertTrue(is_valid_mode("reset"))
        self.assertTrue(is_valid_mode(None))
        self.assertFalse(is_valid_mode("invalid_mode"))

    def test_valid_cluster_wide(self):
        self.assertTrue(is_valid_bool(True))
        self.assertTrue(is_valid_bool(False))
        self.assertFalse(is_valid_bool(1))
        self.assertFalse(is_valid_bool("true"))