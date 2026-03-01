"""
Tests for Tool Registry
"""
import pytest
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tool_registry import Tool, ToolRegistry


class TestToolRegistry:
    """Test tool registry functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        # Use temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.registry = ToolRegistry(Path(self.temp_dir))
    
    def test_register_tool(self):
        """Test registering a new tool"""
        tool = Tool(
            id="",
            name="test_func",
            description="Test function",
            code="def test_func(): return 42",
            parameters={},
            return_type="int",
            created_at=""
        )
        
        tool_id = self.registry.register(tool)
        
        assert tool_id
        assert tool.id == tool_id
        assert self.registry.get(tool_id) == tool
    
    def test_get_by_name(self):
        """Test retrieving tool by name"""
        tool = Tool(
            id="",
            name="my_tool",
            description="Test",
            code="def my_tool(): pass",
            parameters={},
            return_type="None",
            created_at=""
        )
        
        tool_id = self.registry.register(tool)
        retrieved = self.registry.get_by_name("my_tool")
        
        assert retrieved is not None
        assert retrieved.id == tool_id
        assert retrieved.name == "my_tool"
    
    def test_list_tools(self):
        """Test listing all tools"""
        for i in range(3):
            tool = Tool(
                id="",
                name=f"tool_{i}",
                description=f"Tool {i}",
                code=f"def tool_{i}(): pass",
                parameters={},
                return_type="None",
                created_at=""
            )
            self.registry.register(tool)
        
        tools = self.registry.list_tools()
        assert len(tools) == 3
    
    def test_delete_tool(self):
        """Test deleting a tool"""
        tool = Tool(
            id="",
            name="deleteme",
            description="Test",
            code="def deleteme(): pass",
            parameters={},
            return_type="None",
            created_at=""
        )
        
        tool_id = self.registry.register(tool)
        success = self.registry.delete(tool_id)
        
        assert success
        assert self.registry.get(tool_id) is None
    
    def test_update_stats(self):
        """Test updating execution statistics"""
        tool = Tool(
            id="",
            name="stattest",
            description="Test",
            code="def stattest(): pass",
            parameters={},
            return_type="None",
            created_at=""
        )
        
        tool_id = self.registry.register(tool)
        
        # Update stats multiple times
        for _ in range(5):
            self.registry.update_stats(tool_id)
        
        updated_tool = self.registry.get(tool_id)
        assert updated_tool.execution_count == 5
        assert updated_tool.last_executed is not None
    
    def test_search_tools(self):
        """Test searching tools"""
        tools_data = [
            ("calc", "calculator function"),
            ("parse", "parse json data"),
            ("validate", "validate user input")
        ]
        
        for name, desc in tools_data:
            tool = Tool(
                id="",
                name=name,
                description=desc,
                code=f"def {name}(): pass",
                parameters={},
                return_type="None",
                created_at=""
            )
            self.registry.register(tool)
        
        results = self.registry.search("calc")
        assert len(results) == 1
        assert results[0].name == "calc"
        
        results = self.registry.search("data")
        assert len(results) == 1
        assert results[0].name == "parse"
    
    def test_get_stats(self):
        """Test getting registry statistics"""
        # Register some tools
        for i in range(3):
            tool = Tool(
                id="",
                name=f"tool_{i}",
                description=f"Tool {i}",
                code=f"def tool_{i}(): pass",
                parameters={},
                return_type="None",
                created_at="",
                validated=i % 2 == 0  # Alternate validated status
            )
            self.registry.register(tool)
        
        stats = self.registry.get_stats()
        
        assert stats['total_tools'] == 3
        assert stats['validated_tools'] == 2  # 0 and 2 are validated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
