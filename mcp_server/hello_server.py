from mcp.server.mcpserver import MCPServer
mcp = MCPServer("hello")

@mcp.tool()
def hello(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"

@mcp.tool()
def adding_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

if __name__ == "__main__":
    mcp.run()