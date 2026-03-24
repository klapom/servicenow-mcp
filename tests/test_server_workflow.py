"""
Tests for the ServiceNow MCP server workflow management integration.
"""

import unittest

from servicenow_mcp.server import ServiceNowMCP
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


class TestServerWorkflow(unittest.TestCase):
    """Tests for the ServiceNow MCP server workflow management integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.auth_config = AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(username="test_user", password="test_password"),
        )
        self.server_config = ServerConfig(
            instance_url="https://test.service-now.com",
            auth=self.auth_config,
        )
        self.server = ServiceNowMCP(self.server_config)

    def test_register_workflow_tools(self):
        """Test that workflow tools are registered in tool_definitions."""
        workflow_tools = [
            "list_workflows",
            "get_workflow_details",
            "list_workflow_versions",
            "get_workflow_activities",
            "create_workflow",
            "update_workflow",
            "activate_workflow",
            "deactivate_workflow",
            "add_workflow_activity",
            "update_workflow_activity",
            "delete_workflow_activity",
            "reorder_workflow_activities",
        ]

        for tool_name in workflow_tools:
            self.assertIn(
                tool_name,
                self.server.tool_definitions,
                f"Expected workflow tool '{tool_name}' to be registered",
            )

    def test_workflow_tools_enabled_in_full_package(self):
        """Test that workflow tools are enabled in the full package."""
        workflow_tools = [
            "list_workflows",
            "get_workflow_details",
            "create_workflow",
            "update_workflow",
        ]
        for tool_name in workflow_tools:
            self.assertIn(
                tool_name,
                self.server.enabled_tool_names,
                f"Expected workflow tool '{tool_name}' to be enabled in full package",
            )

    def test_workflow_tool_definitions_structure(self):
        """Test that workflow tool definitions have the correct 5-tuple structure."""
        for tool_name in ["list_workflows", "create_workflow"]:
            definition = self.server.tool_definitions[tool_name]
            self.assertEqual(len(definition), 5, f"Expected 5-tuple for {tool_name}")
            impl_func, params_model, return_type, description, serialization = definition
            self.assertTrue(callable(impl_func))
            self.assertIsInstance(description, str)
            self.assertIsInstance(serialization, str)


if __name__ == "__main__":
    unittest.main()
