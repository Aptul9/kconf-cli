# Kubeconfig Management CLI (kconf)

A powerful, cross-platform command-line tool to simplify common Kubernetes kubeconfig management tasks. This tool allows you to easily add, delete, and **export** contexts, as well as manage the `KUBECONFIG` environment variable persistently.

## Installation

This tool is designed to be installed locally from the source code.

1.  **Prerequisites**: Make sure you have Python 3.8 or higher installed.
2.  **Clone the Repository**:
    ```bash
    git clone <your-repository-url>
    cd kconf-cli
    ```
3.  **Install the Tool**: Run the following command from the project's root directory. This command uses the `pyproject.toml` file to install the tool and all its dependencies, making the `kconf` command available system-wide.
    ```bash
    pip install -e .
    ```
    *(The `-e` flag installs it in "editable" mode, meaning any changes you make to the source code will be immediately available without reinstalling.)*

## Usage

The tool is invoked from your terminal using the `kconf` command:

```bash
kconf [GLOBAL_OPTIONS] COMMAND [ARGS]...
```

### Global Options

The following option can be used with the `add`, `delete`, and `export` commands:

-   `--kubeconfig, -k`: Specifies the path to a kubeconfig file to operate on. If not provided, the tool follows the standard Kubernetes precedence:
    1.  The `KUBECONFIG` environment variable.
    2.  The default path at `~/.kube/config`.

---

## Commands

### `add`

Adds a new context, cluster, and user to your kubeconfig from a self-contained YAML file. The tool will check for existing entries and prompt for an override if a conflict is found.

#### **Parameters:**

-   `--file, -f PATH`: **(Required)** The path to the input YAML file containing the new context definition. The file should be structured like a mini-kubeconfig.

#### **Examples:**

```bash
# Add a new context from new-cluster.yaml to the default kubeconfig
kconf add --file new-cluster.yaml

# Add a context using the short flag
kconf add -f new-cluster.yaml

# Add a context to a specific kubeconfig file
kconf --kubeconfig ./custom-config.yaml add -f new-cluster.yaml
```

---

### `delete`

Deletes one or more contexts from your kubeconfig. It performs a "smart delete" by also removing the associated cluster and user definitions, but only if they are no longer used by any other contexts in the file.

#### **Parameters:**

-   `--context, -c TEXT`: **(Required)** The name of the context to delete. This option can be specified multiple times to delete several contexts at once.

#### **Examples:**

```bash
# Delete a single context
kconf delete --context my-dev-context

# Delete multiple contexts in a single command
kconf delete --context staging-context -c another-context
```

---

### `export`

Exports one or more contexts and their related cluster/user definitions into a new, self-contained kubeconfig file. This is useful for sharing access to a specific cluster without sharing your entire configuration.

#### **Parameters:**

-   `--context, -c TEXT`: **(Required)** The name of the context to include in the new file. This can be specified multiple times.
-   `--output, -o PATH`: The path for the new exported kubeconfig file. **(Defaults to `context` in the current directory)**

#### **Examples:**

```bash
# Export a single context into a new file named 'context'
kconf export -c my-prod-context

# Export multiple contexts into a custom-named file
kconf export -c staging-1 -c staging-2 -o staging-kubeconfig.yaml
```

---

### `setkubeconfig`

Sets the `KUBECONFIG` environment variable persistently for your user account. The command automatically detects your operating system and default shell to modify the correct startup file (`~/.bashrc`, `~/.zshrc`, etc., on Linux/macOS) or uses `setx` on Windows.

It joins the provided file paths with the correct OS-specific separator (`:` for Linux/macOS, `;` for Windows).

#### **Parameters:**

-   `--file, -f PATH`: **(Required)** The path to a kubeconfig file to include in the `KUBECONFIG` variable. This option can be specified multiple times. The order matters.

#### **Examples:**

```bash
# Set a single kubeconfig file as the environment variable
kconf setkubeconfig --file ~/.kube/config

# Set multiple kubeconfig files (Linux/macOS example)
# This will result in KUBECONFIG="/path/to/config1:/path/to/config2"
kconf setkubeconfig -f /path/to/config1 -f /path/to/config2

# Set multiple kubeconfig files (Windows example)
# This will result in KUBECONFIG="C:\configs\one.yaml;C:\configs\two.yaml"
kconf setkubeconfig -f C:\configs\one.yaml -f C:\configs\two.yaml
```

> **Note:** After running `setkubeconfig`, you will need to open a **new terminal** or `source` your shell's startup file for the changes to take effect.