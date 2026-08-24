import os
import tempfile
import subprocess
import shutil

class VirtualFileSystem:
    def __init__(self, base_dir="."):
        self.state = {}
        self.base_dir = os.path.abspath(base_dir)
        self._load_substrate()

    def _load_substrate(self):
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
        self.state[rel_path] = content
        return f"VFS Updated: {rel_path}"

    def read_file(self, rel_path):
        return self.state.get(rel_path, f"Error: '{rel_path}' not found in VFS.")

    def simulate_command(self, command, timeout=10):
        temp_dir = tempfile.mkdtemp(prefix="agent_sim_")
        try:
            for rel_path, content in self.state.items():
                full_path = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
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
            return score, output.strip()
            
        except subprocess.TimeoutExpired:
            return 0.0, "Simulation Error: Command timed out."
        finally:
            shutil.rmtree(temp_dir)

    def commit_to_reality(self):
        print("\n[VFS COMMIT] Writing successful simulation back to reality...")
        for rel_path, content in self.state.items():
            full_path = os.path.join(self.base_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        return "Reality updated successfully."