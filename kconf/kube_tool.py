from pathlib import Path
from typing import List, Optional

import typer
import yaml

from .env_manager import set_persistent_kubeconfig
from .kubeconfig_manager import KubeConfigManager
from .utils import load_yaml_file

# Create a Typer application instance
app = typer.Typer(
    name="kube-tool",
    help="A CLI tool to easily manage your Kubernetes kubeconfig file.",
    add_completion=False,
)


# --- NEW: Define a shared context object for our app ---
class AppState:
    def __init__(self):
        self.kubeconfig_path = None


# --- NEW: Create a callback to handle global options ---
@app.callback(invoke_without_command=True)
def main(
        ctx: typer.Context,
        kubeconfig: Optional[Path] = typer.Option(
            None,
            "--kubeconfig",
            "-k",
            help="Path to the kubeconfig file to use. Overrides KUBECONFIG env var and default path.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
):
    """
    Manage your Kubernetes kubeconfig file with ease.
    """
    # This stores the --kubeconfig path in a context object that all commands can access.
    ctx.obj = AppState()
    ctx.obj.kubeconfig_path = kubeconfig

    # If no command is specified, print the help message
    if ctx.invoked_subcommand is None:
        typer.echo("No command specified. Use --help for available commands.")


# --- MODIFIED: Each command now takes 'ctx' as an argument ---
@app.command()
def add(
        ctx: typer.Context,
        file: Path = typer.Option(
            ...,
            "--file",
            "-f",
            help="Path to the YAML file containing the new context definition.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
):
    """
    Adds a new context, cluster, and user to your kubeconfig.
    """
    typer.echo(f"--- Running ADD action for: {file} ---")
    # Pass the global kubeconfig path to the manager
    manager = KubeConfigManager(kubeconfig_path=ctx.obj.kubeconfig_path)

    try:
        new_config_data = load_yaml_file(file)
        if manager.add_context(new_config_data):
            manager.save()
            typer.secho("\n✅ Add operation successful!", fg=typer.colors.GREEN)
        else:
            typer.secho("\n❌ Add operation failed or was aborted by user.", fg=typer.colors.YELLOW)
            raise typer.Abort()
    except ValueError as e:
        typer.secho(f"\nError processing file: {e}", fg=typer.colors.RED)
        raise typer.Abort()


@app.command()
def delete(
        ctx: typer.Context,
        contexts: List[str] = typer.Option(
            ...,
            "--context",
            "-c",
            help="Name of the context to delete. Can be specified multiple times.",
        ),
):
    """
    Deletes one or more contexts from your kubeconfig.
    """
    typer.echo(f"--- Running DELETE action for contexts: {', '.join(contexts)} ---")
    manager = KubeConfigManager(kubeconfig_path=ctx.obj.kubeconfig_path)

    deleted_count = 0
    for context_name in contexts:
        typer.echo(f"\nAttempting to delete '{context_name}'...")
        if manager.delete_context(context_name):
            deleted_count += 1
        else:
            typer.secho(f"Could not delete '{context_name}'. It may not exist.", fg=typer.colors.YELLOW)

    if deleted_count > 0:
        manager.save()
        typer.secho(f"\n✅ Successfully deleted {deleted_count} context(s).", fg=typer.colors.GREEN)
    else:
        typer.secho("\n❌ No contexts were deleted.", fg=typer.colors.RED)


@app.command()
def export(
    ctx: typer.Context,
    contexts: List[str] = typer.Option(
        ...,
        "--context",
        "-c",
        help="Name of the context to export. Can be specified multiple times.",
    ),
    output_file: Path = typer.Option(
        "context",
        "--output",
        "-o",
        help="Path for the new exported kubeconfig file.",
        writable=True,
        dir_okay=False,
    ),
):
    """
    Exports one or more contexts into a new, self-contained kubeconfig file.
    """
    typer.echo(f"--- Running EXPORT action for contexts: {', '.join(contexts)} ---")
    manager = KubeConfigManager(kubeconfig_path=ctx.obj.kubeconfig_path)

    # Call the newly renamed method
    new_config_data = manager.export_contexts(contexts)

    if new_config_data:
        typer.echo(f"Writing new kubeconfig to: {output_file}")
        try:
            with open(output_file, 'w') as f:
                yaml.dump(new_config_data, f, default_flow_style=False, sort_keys=False)
            typer.secho(f"\n✅ Successfully exported kubeconfig to '{output_file}'.", fg=typer.colors.GREEN)
            typer.echo(f"You can use it with: kubectl --kubeconfig {output_file} get pods")
        except IOError as e:
            typer.secho(f"Error: Could not write to file '{output_file}': {e}", fg=typer.colors.RED)
            raise typer.Abort()
    else:
        typer.secho("\n❌ Export operation failed. No contexts were found.", fg=typer.colors.RED)
        raise typer.Abort()

@app.command()
def setkubeconfig(
        files: List[Path] = typer.Option(
            ...,  # This makes the option required
            "--file",
            "-f",
            help="Path to a kubeconfig file to include. Can be specified multiple times.",
            exists=True,  # Typer will check if the file exists
            file_okay=True,  # It must be a file
            dir_okay=False,  # It cannot be a directory
            readable=True,  # It must be readable
        )
):
    """
    Sets the KUBECONFIG environment variable persistently for your shell.

    This command joins the provided file paths with the correct OS-specific
    separator and updates your shell's startup file.
    """
    typer.echo("--- Running SETKUBECONFIG action ---")

    # The 'files' argument is now a list of Path objects
    if set_persistent_kubeconfig(files):
        typer.secho("\n✅ Environment variable set successfully.", fg=typer.colors.GREEN)
    else:
        typer.secho("\n❌ Operation failed. Please check the error messages above.", fg=typer.colors.RED)
        raise typer.Abort()


if __name__ == "__main__":
    app()