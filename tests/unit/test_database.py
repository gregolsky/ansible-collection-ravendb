import sys
from ravendb_test_driver import RavenTestDriver
from unittest import TestCase
from ansible_collections.ravendb.community.plugins.modules.database import (
handle_absent_state , handle_present_state)

class TestDBStateValidator(TestCase):

    def setUp(self):
      super().setUp()
      self.test_driver = RavenTestDriver()

    def test_create_database(self):
        
        store = self.test_driver.get_document_store(database="test_create_database")

        db_name="test_db"
        replication_factor=1
        check_mode=False

        changed, message = handle_present_state(store, db_name, replication_factor, check_mode)
        self.assertTrue(changed)
        self.assertIn(f"Database '{db_name}' created successfully.", message)

    def test_create_already_created_database(self):
      
        store = self.test_driver.get_document_store(database="test_create_already_created_database")

        db_name="test_db1"
        replication_factor=1
        check_mode=False

        changed, message = handle_present_state(store, db_name, replication_factor, check_mode)
        changed, message = handle_present_state(store, db_name, replication_factor, check_mode)

        self.assertFalse(changed)
        self.assertIn(f"Database '{db_name}' already exists.", message)


    def test_delete_database(self):
      
        store = self.test_driver.get_document_store(database="test_delete_database")

        db_name="test_db2"
        replication_factor=1
        check_mode=False

        changed, message = handle_present_state(store, db_name, replication_factor, check_mode)
        changed, message = handle_absent_state(store, db_name, check_mode)

        self.assertTrue(changed)
        self.assertIn(f"Database '{db_name}' deleted successfully.", message)


    def test_delete_non_exist_database(self):
      
        store = self.test_driver.get_document_store(database="test_delete_non_exist_database")

        db_name="test_db3"
        check_mode=False

        changed, message = handle_absent_state(store, db_name, check_mode)

        self.assertFalse(changed)
        self.assertIn(f"Database '{db_name}' does not exist.", message)
