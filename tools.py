"""Tool implementations. All host I/O goes through the VFS, never the live tree."""
import json
import re


def list_files(vfs):
    if not vfs.state:
        return "VFS is empty."
    return "\n".join(sorted(vfs.state.keys()))


def read_file(vfs, filepath):
    content = vfs.read_file(filepath)
    if content.startswith("Error:"):
        return content
    lines = content.split("\n")
    return "".join([f"{i + 1} | {line}\n" for i, line in enumerate(lines)])


def _normalize_written_content(content):
    """Repair common local-model write_file artifacts."""
    if not isinstance(content, str):
        content = "" if content is None else str(content)
    # Entire file arrived as one physical line with escaped newlines.
    if "\\n" in content and "\n" not in content:
        content = (
            content.replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\\'", "'")
            .replace('\\"', '"')
        )
    # Trailing JSON-brace leakage after a complete statement.
    cleaned = re.sub(r"""(['")])\}+\s*$""", r"\1", content.rstrip())
    if cleaned != content.rstrip():
        content = cleaned + ("\n" if content.endswith("\n") else "")
    return content


def write_file(vfs, filepath, content):
    return vfs.write_file(filepath, _normalize_written_content(content))


def search_and_replace(vfs, filepath, old_code, new_code):
    content = vfs.read_file(filepath)
    if content.startswith("Error:"):
        return content
    if not old_code or old_code not in content:
        return (
            "Error: `old_code` block not found exactly as written. "
            "Ensure indentation matches. Prefer `read_file` then full "
            "`write_file` rewrite instead of retrying `search_and_replace`."
        )
    new_content = content.replace(old_code, new_code)
    return vfs.write_file(filepath, new_content)


def run_command(vfs, command):
    score, output = vfs.simulate_command(command)
    status_msg = (
        "[SIMULATION VERIFIED SUCCESS]" if score == 1.0 else "[SIMULATION FAILED]"
    )
    return f"{status_msg}\n\n{output}"


def execute_tool(vfs, tool_name, tool_args):
    if isinstance(tool_args, str):
        try:
            tool_args = json.loads(tool_args)
        except json.JSONDecodeError:
            return "Error: tool_args could not be parsed as JSON."
    if not isinstance(tool_args, dict):
        tool_args = {}

    if tool_name == "list_files":
        return list_files(vfs)
    if tool_name == "read_file":
        return read_file(vfs, tool_args.get("filepath", ""))
    if tool_name == "write_file":
        return write_file(
            vfs, tool_args.get("filepath", ""), tool_args.get("content", "")
        )
    if tool_name == "search_and_replace":
        return search_and_replace(
            vfs,
            tool_args.get("filepath"),
            tool_args.get("old_code"),
            tool_args.get("new_code"),
        )
    if tool_name == "run_command":
        return run_command(vfs, tool_args.get("command", ""))
    return f"Error: The tool '{tool_name}' does not exist."
