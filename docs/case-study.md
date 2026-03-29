# Case Study

This project demonstrates a full reverse-engineering loop with GhidraMCP:

1. Load a target binary into an MCP-enabled Ghidra CodeBrowser.
2. Query functions, strings, xrefs, and decompiler output through the MCP bridge.
3. Recover the expected key from the binary logic.
4. Validate the result by executing the sample.

## Workflow summary

The analysis focused on three key functions:

- `verify_format` establishes the input shape.
- `decode_expected_key` reconstructs the expected secret at runtime.
- `verify_key` compares the provided key with the decoded bytes.

Supporting string and xref data made it easy to narrow the search to the relevant paths in `main`.

## Findings

- The accepted key must begin with `mcp{`, end with `}`, and use alphanumeric or underscore characters in the body.
- The expected body is stored as encoded bytes and decoded with an XOR-by-`0x2A` step.
- Decoding those bytes yields `mcp{MCP_GHIDRA}`.
- Running the binary with that key produces `FLAG{MCP_GHIDRA_NS_2026}`.

## Evidence walkthrough

### 1. MCP-enabled CodeBrowser loaded

![CodeBrowser loaded](screenshots/00_codebrowser_mcp_loaded.png)

This screenshot shows the real Ghidra CodeBrowser instance with the MCP plugin enabled and the sample binary loaded.

### 2. Live MCP tool call

![Live tool call](screenshots/01_task0_tool_call_live.png)

This terminal window captures a real MCP-backed `list_functions()` call against the running Ghidra session.

### 3. Function list

![Function list](screenshots/02_task1_functions_live.png)

The function list identifies the main analysis targets, including `verify_format`, `decode_expected_key`, `verify_key`, and `main`.

### 4. Format validation logic

![verify_format decompile](screenshots/03_task1_key_format_live.png)

The `verify_format` decompile reveals the structural requirements for the accepted input.

### 5. Strings and xrefs

![Strings and xrefs](screenshots/04_task2_strings_xrefs_live.png)

The strings and cross-references highlight the code paths worth following and help connect the HINT strings back to the control flow in `main`.

### 6. Key recovery

![Key recovery](screenshots/05_task2_key_recovery_live.png)

The combined decompile and disassembly evidence show the XOR transformation that recovers the expected key bytes.

### 7. Final validation

![Final validation](screenshots/06_task3_flag_live.png)

The final terminal run verifies the recovered key against the binary and prints the expected flag.
