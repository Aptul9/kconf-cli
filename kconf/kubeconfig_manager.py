import os
import shutil
import sys
from pathlib import Path
import yaml

from .utils import load_yaml_file
from .kubeconfig_operations import KubeConfigOperationsMixin

class KubeConfigManager(KubeConfigOperationsMixin):
    """Manages the state, loading, and saving of a Kubernetes config file."""

    def __init__(self, kubeconfig_path: Path = None):
        """Initializes the manager, resolving the kubeconfig path with standard precedence.

        The path is resolved in the following order:
        1. The explicit `kubeconfig_path` argument.
        2. The `KUBECONFIG` environment variable (using the first path if it's a list).
        3. The default path at `~/.kube/config`.

        Args:
            kubeconfig_path (Path, optional): An explicit path to the kubeconfig.
        """
        # --- CHANGE START ---
        # Resolve the kubeconfig path using standard precedence rules.
        if kubeconfig_path:
            self.path = kubeconfig_path
            print(f"Using explicit kubeconfig path provided: {self.path}")
        elif os.environ.get('KUBECONFIG'):
            env_path_str = os.environ['KUBECONFIG']
            # KUBECONFIG can be a list of paths. Use the first one for modifications.
            first_path_str = env_path_str.split(os.pathsep)[0]
            self.path = Path(first_path_str)
            print(f"Using kubeconfig path from KUBECONFIG environment variable: {self.path}")
        else:
            self.path = Path.home() / ".kube" / "config"
            print(f"Using default kubeconfig path: {self.path}")
        # --- CHANGE END ---

        self.config = self._load()

    def _load(self) -> dict:
        """Loads the kubeconfig file into memory and ensures basic structure."""
        try:
            config_data = load_yaml_file(self.path)
            for key in ['clusters', 'users', 'contexts']:
                if key not in config_data or not isinstance(config_data[key], list):
                    config_data[key] = []
            if 'apiVersion' not in config_data:
                config_data['apiVersion'] = 'v1'
            if 'kind' not in config_data:
                config_data['kind'] = 'Config'
            return config_data
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    def save(self):
        """Creates a backup and saves the current config state to the file."""
        if self.path.exists():
            backup_path = self.path.with_suffix(f"{self.path.suffix}.bak")
            print(f"Backing up current kubeconfig to {backup_path}")
            try:
                shutil.copy(self.path, backup_path)
            except OSError as e:
                print(f"Error: Could not create backup: {e}", file=sys.stderr)
                sys.exit(1)

        print(f"Writing updated configuration to {self.path}")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        except IOError as e:
            print(f"Error: Could not write to kubeconfig file: {e}", file=sys.stderr)
            sys.exit(1)