import os
import re
import tempfile
import subprocess
import shutil

VERIFICATION_COMMAND_RE = re.compile(
    r"(pytest|\-m\s+unittest|unittest|python3?(?:\s+\S+)*\s+test_\S+\.py)",
    re.IGNORECASE,
)


def is_verification_command(command):
    """True when a shell command is a test/verification rollout, not a generic shell step."""
    if not command or not isinstance(command, str):
        return False
    return bool(VERIFICATION_COMMAND_RE.search(command))


is_verification_command = is_verification_command


class VirtualFileSystem:
    def __init__(self, base_dir="."):
        self.state = {}
        self.base_dir = os.path.abspath(base_dir)
        self.touched_paths = set()
        self.command_history = []
        self._load_substrate()

    def _resolve_rel(self, rel_path):
        if not rel_path or not isinstance(rel_path, str):
            return None
        full_path = os.path.abspath(os.path.join(self.base_dir, rel_path))
        if full_path != self.base_dir and not full_path.startswith(self.base_dir + os.sep):
            return None
        return os.path.relpath(full_path, self.base_dir)

    def _load_substrate(self):
        if not os.path.isdir(self.base_dir):
            return
        for root, dirs, files in os.walk(self.base_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules')]
            for file in files:
                if file.startswith('.'):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.base_dir)
                try:
                    with open(full_path, 'r') as f:
                        self.state[rel_path] = f.read()
                except UnicodeDecodeError:
                    pass

    def write_file(self, rel_path, content):
        safe_path = self._resolve_rel(rel_path)
        if safe_path is None:
            return f"Error: path '{rel_path}' is outside the workspace."
        self.state[safe_path] = content
        self.touched_paths.add(safe_path)
        return f"VFS Updated: {safe_path}"

    def read_file(self, rel_path):
        safe_path = self._resolve_rel(rel_path)
        if safe_path is None:
            return f"Error: '{rel_path}' not found in VFS."
        return self.state.get(safe_path, f"Error: '{safe_path}' not found in VFS.")

    def record_command(self, command, score):
        self.command_history.append({"command": command, "score": float(score)})

    def last_command(self):
        if not self.command_history:
            return None
        return self.command_history[-1]

    def verified_command(self):
        last = self.last_command()
        if last and is_verification_command(last["command"]) and last["score"] == 1.0:
            return last["command"]
        return None

    def is_task_verified(self):
        """Last command must be a passing test/verification rollout."""
        return self.verified_command() is not None

    def simulate_command(self, command, timeout=10):
        temp_dir = tempfile.mkdtemp(prefix="agent_sim_")
        try:
            for rel_path, content in self.state.items():
                full_path = os.path.join(temp_dir, rel_path)
                parent = os.path.dirname(full_path)
                if parent:
                    os.makedirs(parent, exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)

            result = subprocess.run(
                command,
                shell=True,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            score = 1.0 if result.returncode == 0 else 0.0
            output = result.stdout + "\n" + result.stderr
            self.record_command(command, score)
            return score, output.strip()

        except subprocess.TimeoutExpired:
            self.record_command(command, 0.0)
            return 0.0, "Simulation Error: Command timed out."
        finally:
            shutil.rmtree(temp_dir)

    def commit_to_reality(self):
        if not self.is_task_verified():
            print("\n[VFS COMMIT BLOCKED] Refusing to write unverified VFS state to disk.")
            return False

        print("\n[VFS COMMIT] Writing agent-touched files back to reality...")
        written = 0
        for rel_path in sorted(self.touched_paths):
            content = self.state.get(rel_path)
            if content is None:
                continue
            full_path = os.path.join(self.base_dir, rel_path)
            parent = os.path.dirname(full_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            written += 1
        print(f"[VFS COMMIT] {written} file(s) written.")
        return True

    # Test / older-call-site aliases
    write_file = write_file
    commit_to_reality = commit_to_reality
    is_task_verified = is_task_verified
    record_command = record_command
    last_command = last_command
    verified_command = verified_command
    simulate_command = simulate_command
