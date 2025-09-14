import asyncio
import os
from dataclasses import dataclass
from typing import Any, AsyncContextManager

from mcp.server.fastmcp import FastMCP
from multilspy import LanguageServer
from multilspy.multilspy_config import Language, MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from multilspy.multilspy_types import SymbolKind, CompletionItemKind

# Create an MCP server
mcp = FastMCP("MultilspyLSP")


@dataclass
class LspSession:
    """Active language server session with associated project root."""

    language_server: LanguageServer
    project_root: str
    language: Language
    context: AsyncContextManager[LanguageServer]


# Global mapping of session_id to language server instances
lsp_sessions: dict[str, LspSession] = {}


@mcp.tool()
async def initialize_language_server(
    session_id: str,
    project_root: str,
    language: str,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Initialize a language server for the specified language and project.

    Parameters:
        session_id: Unique identifier for this language server session
        project_root: Absolute path to the project root directory
        language: Programming language to initialize the server for (e.g., "python", "java", "typescript")
        debug: Enable debug logging

    Returns:
        Dictionary containing session info and initialization status
    """
    # Validate the language is supported
    try:
        lang = Language(language.lower())
    except ValueError:
        supported = [l.value for l in Language]
        return {
            "success": False,
            "error": f"Unsupported language: {language}. Supported languages: {', '.join(supported)}"
        }

    # Validate project root exists
    if not os.path.isdir(project_root):
        return {
            "success": False,
            "error": f"Project root directory does not exist: {project_root}"
        }

    # Initialize config and logger
    config = MultilspyConfig(
        code_language=lang,
        trace_lsp_communication=debug,
        start_independent_lsp_process=True,
    )

    logger = MultilspyLogger()

    try:
        # Create language server
        lsp = LanguageServer.create(config, logger, project_root)

        # Start the server
        context = lsp.start_server()
        await context.__aenter__()

        # Store the session
        lsp_sessions[session_id] = LspSession(
            language_server=lsp,
            project_root=project_root,
            language=lang,
            context=context,
        )

        return {
            "success": True,
            "session_id": session_id,
            "language": language,
            "project_root": project_root
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to initialize language server: {str(e)}"
        }


@mcp.tool()
async def shutdown_language_server(session_id: str) -> dict[str, Any]:
    """
    Shutdown a language server session.

    Parameters:
        session_id: The session ID returned from initialize_language_server

    Returns:
        Dictionary indicating success or failure
    """
    if session_id not in lsp_sessions:
        return {
            "success": False,
            "error": f"Session not found: {session_id}"
        }

    try:
        # Perform cleanup
        await lsp_sessions[session_id].context.__aexit__(None, None, None)
        del lsp_sessions[session_id]
        return {
            "success": True
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to shutdown language server: {str(e)}"
        }


@mcp.tool()
async def request_definition(
    session_id: str,
    file_path: str,
    line: int,
    column: int
) -> dict[str, Any]:
    """
    Find the definition of a symbol at the specified location.

    Parameters:
        session_id: The session ID returned from initialize_language_server
        file_path: Path to the file containing the symbol, relative to project root
        line: Line number (0-indexed)
        column: Column number (0-indexed)

    Returns:
        Definition information for the symbol
    """
    if session_id not in lsp_sessions:
        return {
            "success": False,
            "error": f"Session not found: {session_id}"
        }

    session = lsp_sessions[session_id]
    lsp = session.language_server

    try:
        with lsp.open_file(file_path):
            result = await lsp.request_definition(file_path, line, column)

            if not result:
                return {
                    "success": True,
                    "found": False,
                    "definitions": []
                }

            # Convert definitions to a more usable format
            definitions = []
            for definition in result:
                definition["uri"] = definition["uri"].replace("file://", "")

            return {
                "success": True,
                "found": True,
                "definitions": definitions
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get definition: {str(e)}"
        }


@mcp.tool()
async def request_references(
    session_id: str,
    file_path: str,
    line: int,
    column: int
) -> dict[str, Any]:
    """
    Find all references of a symbol at the specified location.

    Parameters:
        session_id: The session ID returned from initialize_language_server
        file_path: Path to the file containing the symbol, relative to project root
        line: Line number (0-indexed)
        column: Column number (0-indexed)

    Returns:
        References information for the symbol
    """
    if session_id not in lsp_sessions:
        return {
            "success": False,
            "error": f"Session not found: {session_id}"
        }

    session = lsp_sessions[session_id]
    lsp = session.language_server

    try:
        with lsp.open_file(file_path):
            result = await lsp.request_references(file_path, line, column)

            if not result:
                return {
                    "success": True,
                    "found": False,
                    "references": []
                }

            # Convert references to a more usable format
            references = []
            for reference in result:
                reference["uri"] = reference["uri"].replace("file://", "")

            return {
                "success": True,
                "found": True,
                "references": references
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get references: {str(e)}"
        }


@mcp.tool()
async def request_completions(
    session_id: str,
    file_path: str,
    line: int,
    column: int
) -> dict[str, Any]:
    """
    Get completion suggestions for a location in the code.

    Parameters:
        session_id: The session ID returned from initialize_language_server
        file_path: Path to the file containing the location, relative to project root
        line: Line number (0-indexed)
        column: Column number (0-indexed)

    Returns:
        Completion suggestions for the location
    """
    if session_id not in lsp_sessions:
        return {
            "success": False,
            "error": f"Session not found: {session_id}"
        }

    session = lsp_sessions[session_id]
    lsp = session.language_server

    try:
        with lsp.open_file(file_path):
            result = await lsp.request_completions(file_path, line, column)

            if not result:
                return {
                    "success": True,
                    "found": False,
                    "completions": []
                }

            # Convert completions to a more usable format
            completions = []
            for item in result:
                completions.append({
                    "text": item["completionText"],
                    "kind": CompletionItemKind(item["kind"]).name,
                    "detail": item.get("detail", ""),
                })

            return {
                "success": True,
                "found": True,
                "completions": completions
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get completions: {str(e)}"
        }


@mcp.tool()
async def request_hover(
    session_id: str,
    file_path: str,
    line: int,
    column: int
) -> dict[str, Any]:
    """
    Get hover information for a symbol at the specified location.

    Parameters:
        session_id: The session ID returned from initialize_language_server
        file_path: Path to the file containing the symbol, relative to project root
        line: Line number (0-indexed)
        column: Column number (0-indexed)

    Returns:
        Hover information for the symbol
    """
    if session_id not in lsp_sessions:
        return {
            "success": False,
            "error": f"Session not found: {session_id}"
        }

    session = lsp_sessions[session_id]
    lsp = session.language_server

    try:
        with lsp.open_file(file_path):
            result = await lsp.request_hover(file_path, line, column)

            if not result or not result["contents"]:
                return {
                    "success": True,
                    "found": False,
                    "hover": None
                }

            # Extract hover content
            contents = result["contents"]
            if isinstance(contents, dict):
                content = contents.get("value")
            elif isinstance(contents, list):
                content = ""
                for i, item in enumerate(contents):
                    if i > 0:
                        content += "\n"
                    if isinstance(item, dict):
                        value = item.get("value")
                    else:
                        value = str(item)
                    content += value
            else:
                content = str(contents)

            return {
                "success": True,
                "found": True,
                "hover": {
                    "content": content
                }
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get hover information: {str(e)}"
        }


@mcp.tool()
async def request_document_symbols(
    session_id: str,
    file_path: str
) -> dict[str, Any]:
    """
    Get all symbols defined in a document.

    Parameters:
        session_id: The session ID returned from initialize_language_server
        file_path: Path to the file to analyze, relative to project root

    Returns:
        Symbols defined in the document
    """
    if session_id not in lsp_sessions:
        return {
            "success": False,
            "error": f"Session not found: {session_id}"
        }

    session = lsp_sessions[session_id]
    lsp = session.language_server

    try:
        with lsp.open_file(file_path):
            result, _ = await lsp.request_document_symbols(file_path)

            if not result:
                return {
                    "success": True,
                    "found": False,
                    "symbols": []
                }

            # Reduce the amount of information returned
            for symbol in result:
                if "containerName" in symbol:
                    del symbol["containerName"]
                symbol["kind"] = SymbolKind(symbol["kind"]).name
                if "location" in symbol:
                    location = symbol["location"]
                    if "uri" in location:
                        del location["uri"]

            return {
                "success": True,
                "found": True,
                "symbols": result,
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get document symbols: {str(e)}"
        }


@mcp.tool()
async def request_workspace_symbol(
    session_id: str,
    query: str,
):
    """
    Find a symbol in the code.

    Parameters:
        query: The symbol to search for

    Returns:
        The symbol location
    """
    if session_id not in lsp_sessions:
        return {
            "success": False,
            "error": f"Session not found: {session_id}"
        }

    session = lsp_sessions[session_id]
    lsp = session.language_server

    try:
        result = await lsp.request_workspace_symbol(query)
        if not result:
            return {
                "success": True,
                "found": False,
                "symbols": [],
            }

        # Reduce the amount of information returned
        for symbol in result:
            if "containerName" in symbol:
                del symbol["containerName"]
            symbol["kind"] = SymbolKind(symbol["kind"]).name
            if "location" in symbol:
                location = symbol["location"]
                if "uri" in location:
                    del location["uri"]

        return {
            "success": True,
            "found": True,
            "symbols": result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get document symbols: {str(e)}"
        }


@mcp.resource("multilspy://languages")
def get_supported_languages() -> dict[str, Any]:
    """
    Get a list of programming languages supported by the multilspy server.

    Returns:
        Dictionary of supported languages and their descriptions
    """
    languages = {
        "java": "Java support using Eclipse JDTLS",
        "python": "Python support using jedi-language-server",
        "rust": "Rust support using Rust Analyzer",
        "csharp": "C# support using OmniSharp/RazorSharp",
        "typescript": "TypeScript support using TypeScriptLanguageServer",
        "javascript": "JavaScript support using TypeScriptLanguageServer",
        "go": "Go support using gopls",
        "dart": "Dart support using Dart Language Server",
        "ruby": "Ruby support using Solargraph",
        "kotlin": "Kotlin support using kotlin-language-server",
        "cpp": "C++ support using clangd",
    }

    return {
        "supported_languages": languages
    }


@mcp.prompt()
def get_started() -> str:
    """
    Returns a prompt to help users get started with the multilspy MCP server.
    """
    return """
# MultilspyLSP MCP Server

This server provides Language Server Protocol (LSP) functionality via multilspy.

## Getting Started

First, initialize a language server session:

```python
# Initialize a Python language server session
result = await initialize_language_server(
    session_id="my-session-1",
    project_root="/path/to/your/project",
    language="python"
)
```

Then, use the session to get language intelligence:

```python
# Find where a symbol is defined
definitions = await request_definition(
    session_id="my-session-1",
    file_path="src/main.py",
    line=10,  # 0-indexed
    column=15  # 0-indexed
)

# Get code completion suggestions
completions = await request_completions(
    session_id="my-session-1",
    file_path="src/main.py",
    line=10,
    column=15
)
```

Remember to shut down the session when done:

```python
await shutdown_language_server(session_id="my-session-1")
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
- Kotlin (kotlin-language-server)
- C++ (clangd)
"""


async def cleanup_language_servers():
    """Clean up any remaining language servers."""
    for session in lsp_sessions.values():
        await session.context.__aexit__(None, None, None)
    lsp_sessions.clear()


def main() -> None:
    """Run the MCP server."""
    try:
        mcp.run()
    finally:
        asyncio.run(cleanup_language_servers())


if __name__ == "__main__":
    main()
