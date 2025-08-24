from pathlib import Path
import yaml

def load_yaml_file(path: Path) -> dict:
    """Loads a YAML file and returns its content as a dictionary.

    Args:
        path (Path): The path to the YAML file.

    Returns:
        dict: The parsed content of the YAML file.

    Raises:
        ValueError: If the YAML file cannot be parsed.
    """
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Could not parse YAML file at {path}: {e}") from e

def find_item_by_name(item_list: list, name: str) -> tuple[int, dict | None]:
    """Finds an item in a list of dictionaries by its 'name' key.

    Args:
        item_list (list): The list of dictionaries to search through.
        name (str): The value of the 'name' key to find.

    Returns:
        tuple[int, dict | None]: A tuple containing the index and the item
                                 if found, otherwise (-1, None).
    """
    for i, item in enumerate(item_list):
        if item.get("name") == name:
            return i, item
    return -1, None

def prompt_for_override(item_type: str, name: str) -> bool:
    """Asks the user for confirmation to override an existing item via stdin.

    Args:
        item_type (str): The type of the item (e.g., 'cluster', 'context').
        name (str): The name of the item.

    Returns:
        bool: True if the user confirms, False otherwise.
    """
    response = input(f"A {item_type} named '{name}' already exists. Override? [y/N]: ").lower().strip()
    return response in ['y', 'yes']