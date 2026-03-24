"""
Tests for the ServiceNow MCP server integration with catalog functionality.
"""

import unittest

from servicenow_mcp.server import ServiceNowMCP


class TestServerCatalog(unittest.TestCase):
    """Test cases for the server integration with catalog functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "instance_url": "https://example.service-now.com",
            "auth": {
                "type": "basic",
                "basic": {
                    "username": "admin",
                    "password": "password",
                },
            },
        }
        self.server = ServiceNowMCP(self.config)

    def test_catalog_tools_registered(self):
        """Test that catalog tools are registered in tool_definitions."""
        expected_tools = [
            "list_catalog_items",
            "get_catalog_item",
            "list_catalog_categories",
            "create_catalog_category",
            "update_catalog_category",
            "move_catalog_items",
        ]
        for tool_name in expected_tools:
            self.assertIn(
                tool_name,
                self.server.tool_definitions,
                f"Expected tool '{tool_name}' to be registered",
            )

    def test_list_catalog_items_tool_definition(self):
        """Test the list_catalog_items tool definition has correct structure."""
        definition = self.server.tool_definitions["list_catalog_items"]
        impl_func, params_model, return_type, description, serialization = definition
        self.assertTrue(callable(impl_func))
        self.assertIn("catalog", description.lower())

    def test_get_catalog_item_tool_definition(self):
        """Test the get_catalog_item tool definition has correct structure."""
        definition = self.server.tool_definitions["get_catalog_item"]
        impl_func, params_model, return_type, description, serialization = definition
        self.assertTrue(callable(impl_func))
        self.assertIn("catalog", description.lower())

    def test_list_catalog_categories_tool_definition(self):
        """Test the list_catalog_categories tool definition has correct structure."""
        definition = self.server.tool_definitions["list_catalog_categories"]
        impl_func, params_model, return_type, description, serialization = definition
        self.assertTrue(callable(impl_func))
        self.assertIn("catalog", description.lower())

    def test_catalog_tools_in_full_package_config(self):
        """Test that catalog tools are listed in the full package definition."""
        full_package = self.server.package_definitions.get("full", [])
        catalog_tools = [
            "list_catalog_items",
            "get_catalog_item",
            "list_catalog_categories",
        ]
        for tool_name in catalog_tools:
            self.assertIn(
                tool_name,
                full_package,
                f"Expected tool '{tool_name}' in full package definition",
            )


if __name__ == "__main__":
    unittest.main()
