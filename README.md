# MCP-MultilspyLSP

An MCP server that exposes Language Server Protocol (LSP) capabilities through multilspy.

## What is this?

This project provides an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that
gives language models access to language intelligence features from the Language Server Protocol (LSP).
It uses [multilspy](https://github.com/microsoft/multilspy), a Python library that simplifies
interfacing with various language servers.

## Features

- **Language Intelligence**: Get code completions, find definitions, references, and more
- **Multi-language Support**: Works with multiple programming languages including Python, Java, TypeScript, and more
- **Easy Integration**: Works with any MCP-compatible client like Claude Desktop
- **Static Analysis**: Leverage the power of language servers for code understanding

## Installation

```bash
pip install mcp-multilspy
```

## Usage

Start the server directly:

```bash
mcp-multilspy
```

Or install it in Claude Desktop:

```bash
mcp install mcp-multilspy
```

## Supported Languages

- Java (Eclipse JDTLS)
- Python (jedi-language-server)
- Rust (Rust Analyzer)
- C# (OmniSharp/RazorSharp)
- TypeScript (TypeScriptLanguageServer)
- JavaScript (TypeScriptLanguageServer)
- Go (gopls)
- Dart (Dart Language Server)
- Ruby (Solargraph)
- Kotlin
- C++ (clangd)

## Example

Here's how to use this server with an MCP client:

```python
# Initialize a TypeScript language server session
session = await initialize_language_server(
    session_id="ts-session", 
    project_root="/path/to/project",
    language="typescript"
)

# Find where a symbol is defined
definitions = await request_definition(
    session_id="ts-session",
    file_path="src/index.ts",
    line=10,  # 0-indexed
    column=15  # 0-indexed
)

# Find all references to a symbol
references = await request_references(
    session_id="ts-session",
    file_path="src/index.ts",
    line=10,
    column=15
)

# Get code completion suggestions
completions = await request_completions(
    session_id="ts-session",
    file_path="src/index.ts", 
    line=10,
    column=15
)

# Get hover information
hover_info = await request_hover(
    session_id="ts-session",
    file_path="src/index.ts",
    line=10,
    column=15
)

# Get document symbols
symbols = await request_document_symbols(
    session_id="ts-session",
    file_path="src/index.ts"
)

# Clean up when done
await shutdown_language_server(session_id="ts-session")
```

## Requirements

- Python 3.12 or higher
- Language-specific requirements:
  - For Java: JDK 17.0.6 or higher
  - For JavaScript/TypeScript: Node.js v18.16.0 or higher

## License

MIT