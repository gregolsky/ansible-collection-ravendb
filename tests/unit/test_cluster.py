# Copyright (c), RavenDB
# GNU General Public License v3.0 or later (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from unittest import TestCase
from unittest.mock import patch, Mock
from ansible_collections.community.ravendb.plugins.modules.node import add_node, is_valid_url, is_valid_tag
import requests


class TestAddNodeWithRavenDB(TestCase):

    def setUp(self):
        self.leader_url = "http://localhost:8080"

    def test_add_node_success(self):
        node = {
            "url": "http://localhost:8081",
            "tag": "B",
            "leader_url": self.leader_url,
            "type": "Member"
        }
        with patch("requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_put.return_value = mock_response

            result = add_node(node, check_mode=False)
            self.assertTrue(result["changed"])
            self.assertEqual(result["msg"], "Node B added to the cluster")

    def test_add_node_check_mode(self):
        node = {
            "url": "http://localhost:8081",
            "tag": "B",
            "leader_url": self.leader_url,
            "type": "Member"
        }
        result = add_node(node, check_mode=True)
        self.assertTrue(result["changed"])
        self.assertEqual(result["msg"], "Node B would be added to the cluster")

    def test_add_node_invalid_url(self):
        node = {
            "url": "invalid-url",
            "tag": "C",
            "leader_url": self.leader_url,
            "type": "Member"
        }
        result = add_node(node, check_mode=False)
        self.assertFalse(result["changed"])
        self.assertEqual(
            result["msg"],
            "Invalid URL: must be a valid HTTP(S) URL")

    def test_add_node_invalid_tag(self):
        node = {
            "url": "http://localhost:8081",
            "tag": "bagheera",
            "leader_url": self.leader_url,
            "type": "Member"
        }
        result = add_node(node, check_mode=False)
        self.assertFalse(result["changed"])
        self.assertEqual(
            result["msg"],
            "Invalid tag: Node tag must be an uppercase non-empty alphanumeric string")

    def test_add_watcher_node(self):
        node = {
            "url": "http://localhost:8083",
            "tag": "D",
            "leader_url": self.leader_url,
            "type": "Watcher"
        }
        with patch("requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_put.return_value = mock_response

            result = add_node(node, check_mode=False)
            self.assertTrue(result["changed"])
            self.assertEqual(result["msg"], "Node D added to the cluster")

    def test_add_already_added_node(self):
        node = {
            "url": "http://localhost:8081",
            "tag": "A",
            "leader_url": self.leader_url,
            "type": "Member"
        }
        with patch("requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                "System.InvalidOperationException: Can't add a new node")
            mock_put.return_value = mock_response

            result = add_node(node, check_mode=False)

            self.assertFalse(result["changed"])
            self.assertIn("Failed to add node A", result["msg"])

    def test_add_node_with_existing_tag_different_url(self):
        node = {
            "url": "http://localhost:9090",
            "tag": "A",
            "leader_url": self.leader_url,
            "type": "Member"
        }
        with patch("requests.put") as mock_put:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError(
                "System.InvalidOperationException: Was requested to modify the topology for node...")
            mock_put.return_value = mock_response

            result = add_node(node, check_mode=False)
            self.assertFalse(result["changed"])
            self.assertIn("Failed to add node A", result["msg"])


class TestValidationFunctions(TestCase):
    def test_valid_url(self):
        self.assertTrue(is_valid_url("https://example.com"))
        self.assertTrue(is_valid_url("http://localhost:8080"))
        self.assertFalse(is_valid_url("example.com"))
        self.assertFalse(is_valid_url("://invalid-url"))
        self.assertFalse(is_valid_url(123))

    def test_valid_tag(self):
        self.assertTrue(is_valid_tag("NODE1"))
        self.assertTrue(is_valid_tag("CLUSTERX"))
        self.assertFalse(is_valid_tag("node1"))
        self.assertFalse(is_valid_tag("NODE-1"))
        self.assertFalse(is_valid_tag(""))
        self.assertFalse(is_valid_tag(123))
