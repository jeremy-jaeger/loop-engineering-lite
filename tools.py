import json

def list_files(vfs):
    """Reads the keys from the VFS dictionary to show the agent what files exist."""
    if not vfs.state:
        return "VFS is empty."
    return "\n".join(sorted(vfs.state.keys()))

def read_file(vfs, filepath):
    """Reads a file from the VFS memory and prepends line numbers."""
    content = vfs.read_file(filepath)
    if content.startswith("Error:"):
        return content
        
    lines = content.split('\n')
    return "".join([f"{i+1} | {line}\n" for i, line in enumerate(lines)])

def _normalize_written_content(content):
    """Repair common local-LLM write_file artifacts."""
    import re as _re

    if not isinstance(content, str):
        content = "" if content is None else str(content)
    # Double-escaped newlines: entire file arrives as one physical line with \n.
    if "\\n" in content and "\n" not in content:
        content = (
            content.replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\\'", "'")
            .replace('\\"', '"')
        )
    # Trailing JSON-brace leakage after a complete statement (e.g. "...'-')}}}").
    cleaned = _re.sub(r'''(['")])\}+\s*$''', r"\1", content.rstrip())
    if cleaned != content.rstrip():
        content = cleaned + ("\n" if content.endswith("\n") else "")
    return content


def write_file(vfs, filepath, content):
    """Writes directly to the VFS dictionary."""
    return vfs.write_file(filepath, _normalize_written_content(content))

def search_and_replace(vfs, filepath, old_code, new_code):
    """Performs a surgical edit on a file living in the VFS dictionary."""
    content = vfs.read_file(filepath)
    if content.startswith("Error:"):
        return content
        
    if old_code not in content:
        return (
            "Error: `old_code` block not found exactly as written. "
            "Ensure indentation matches. Prefer `read_file` then full "
            "`write_file` rewrite instead of retrying `search_and_replace`."
        )
        
    new_content = content.replace(old_code, new_code)
    return vfs.write_file(filepath, new_content)

def run_command(vfs, command):
    """
    Triggers the World Model rollout. 
    It evaluates the state, returns the score, and formats it for the LLM.
    """
    score, output = vfs.simulate_command(command)
    
    # We explicitly tell the LLM if the simulation passed or failed
    status_msg = "[SIMULATION VERIFIED SUCCESS]" if score == 1.0 else "[SIMULATION FAILED]"
    return f"{status_msg}\n\n{output}"

def execute_tool(vfs, tool_name, tool_args):
    """Routes the LLM's requested action, passing the VFS instance to the tool."""
    if isinstance(tool_args, str):
        try:
            tool_args = json.loads(tool_args)
        except json.JSONDecodeError:
            return "Error: tool_args could not be parsed as JSON."

    if tool_name == "list_files":
        return list_files(vfs)
    elif tool_name == "read_file":
        return read_file(vfs, tool_args.get("filepath", ""))
    elif tool_name == "write_file":
        return write_file(vfs, tool_args.get("filepath", ""), tool_args.get("content", ""))
    elif tool_name == "search_and_replace":
        return search_and_replace(vfs, tool_args.get("filepath"), tool_args.get("old_code"), tool_args.get("new_code"))
    elif tool_name == "run_command":
        return run_command(vfs, tool_args.get("command", ""))
    else:
        return f"Error: The tool '{tool_name}' does not exist."