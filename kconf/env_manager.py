import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List  # Add this import


def _set_windows_env(value: str) -> bool:
    """Sets the KUBECONFIG environment variable persistently on Windows using setx."""
    print("Detected Windows OS. Using 'setx' to set the environment variable.")
    try:
        # The command is `setx VARIABLE "VALUE"`
        # We use subprocess.run to execute it.
        subprocess.run(["setx", "KUBECONFIG", value], capture_output=True, text=True, check=True)
        print("Successfully executed setx command.")
        print("\nIMPORTANT: The new environment variable will be available in any NEW terminal you open.")
        return True
    except FileNotFoundError:
        print("Error: 'setx' command not found. It might not be in your system's PATH.", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error executing 'setx': {e.stderr}", file=sys.stderr)
        return False


def _set_unix_env(value: str) -> bool:
    """Sets the KUBECONFIG environment variable persistently on Unix-like systems."""
    shell_name = os.environ.get("SHELL", "").split('/')[-1]
    print(f"Detected Unix-like OS with shell: {shell_name}")

    # Map shell names to their common startup files and export commands
    shell_configs = {
        'bash': {'file': '.bashrc', 'command': f'export KUBECONFIG="{value}"'},
        'zsh': {'file': '.zshrc', 'command': f'export KUBECONFIG="{value}"'},
        'fish': {'file': '.config/fish/config.fish', 'command': f'set -x KUBECONFIG "{value}"'},
    }

    if shell_name not in shell_configs:
        print(f"Error: Unsupported shell '{shell_name}'.", file=sys.stderr)
        print("Please manually add the export command to your shell's startup file.", file=sys.stderr)
        return False

    config = shell_configs[shell_name]
    config_file_path = Path.home() / config['file']
    export_command = config['command']

    print(f"Updating shell configuration file: {config_file_path}")

    try:
        lines = config_file_path.read_text().splitlines() if config_file_path.exists() else []
        found_and_updated = False

        for i, line in enumerate(lines):
            if line.strip().startswith(('export KUBECONFIG=', 'set -x KUBECONFIG')):
                lines[i] = export_command
                found_and_updated = True
                print("Found and updated existing KUBECONFIG definition.")
                break

        if not found_and_updated:
            lines.append('')  # Add a blank line for separation
            lines.append(export_command)
            print("Added new KUBECONFIG definition to the end of the file.")

        config_file_path.write_text('\n'.join(lines) + '\n')

        print("\nIMPORTANT: To apply changes, run the following command or open a new terminal:")
        print(f"  source {config_file_path}")
        return True

    except IOError as e:
        print(f"Error: Could not write to '{config_file_path}': {e}", file=sys.stderr)
        return False


def set_persistent_kubeconfig(file_paths: List[Path]) -> bool:
    """
    Sets the KUBECONFIG environment variable persistently across platforms.

    Args:
        file_paths (List[Path]): A list of Path objects for the kubeconfig files.

    Returns:
        bool: True if the operation was successful, False otherwise.
    """
    # Construct the KUBECONFIG string by joining absolute paths with the OS-specific separator
    # os.pathsep is ':' on Unix and ';' on Windows.
    # .resolve() ensures we use absolute paths, which is more robust.
    kubeconfig_value = os.pathsep.join([str(p.resolve()) for p in file_paths])
    print(f"Constructed KUBECONFIG value: {kubeconfig_value}")

    system = platform.system()
    if system == "Windows":
        return _set_windows_env(kubeconfig_value)
    elif system in ["Linux", "Darwin"]:  # Darwin is macOS
        return _set_unix_env(kubeconfig_value)
    else:
        print(f"Error: Unsupported operating system '{system}'.", file=sys.stderr)
        return False