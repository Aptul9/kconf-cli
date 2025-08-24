import sys
from .utils import find_item_by_name, prompt_for_override


class KubeConfigOperationsMixin:
    """
    A mixin class containing high-level operations for a KubeConfigManager.

    This class assumes it is mixed into a class that has a `self.config`
    dictionary representing the kubeconfig data.
    """

    config: dict

    def add_context(self, new_config_data: dict) -> bool:
        """Adds a new cluster, user, and context, checking for duplicates.

        Args:
            new_config_data (dict): A dictionary containing the new context info.

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        try:
            new_cluster = new_config_data['clusters'][0]
            new_user = new_config_data['users'][0]
            new_context = new_config_data['contexts'][0]
        except (KeyError, IndexError, TypeError):
            print("Error: Input data is malformed. Expected 'clusters', 'users', and 'contexts' keys.", file=sys.stderr)
            return False

        items_to_process = [
            ("cluster", new_cluster, self.config['clusters']),
            ("user", new_user, self.config['users']),
            ("context", new_context, self.config['contexts']),
        ]

        for item_type, new_item, main_list in items_to_process:
            item_name = new_item['name']
            index, existing_item = find_item_by_name(main_list, item_name)

            if existing_item:
                if prompt_for_override(item_type, item_name):
                    print(f"Updating existing {item_type} '{item_name}'...")
                    main_list[index] = new_item
                else:
                    print(f"Skipping {item_type} '{item_name}'. Aborting add operation.")
                    return False
            else:
                print(f"Adding new {item_type} '{item_name}'...")
                main_list.append(new_item)
        return True

    def delete_context(self, context_name: str) -> bool:
        """Deletes a context and its associated user and cluster if they are not in use.

        Args:
            context_name (str): The name of the context to delete.

        Returns:
            bool: True if the context was found and deleted, False otherwise.
        """
        context_index, context_to_delete = find_item_by_name(self.config['contexts'], context_name)
        if not context_to_delete:
            print(f"Error: Context '{context_name}' not found.", file=sys.stderr)
            return False

        cluster_name = context_to_delete['context']['cluster']
        user_name = context_to_delete['context']['user']

        print(f"Deleting context '{context_name}'...")
        self.config['contexts'].pop(context_index)

        is_cluster_used = any(c['context']['cluster'] == cluster_name for c in self.config['contexts'])
        is_user_used = any(c['context']['user'] == user_name for c in self.config['contexts'])

        if not is_cluster_used:
            cluster_index, _ = find_item_by_name(self.config['clusters'], cluster_name)
            if cluster_index != -1:
                print(f"Deleting unused cluster '{cluster_name}'...")
                self.config['clusters'].pop(cluster_index)
        else:
            print(f"Info: Cluster '{cluster_name}' is still in use by another context, not deleting.")

        if not is_user_used:
            user_index, _ = find_item_by_name(self.config['users'], user_name)
            if user_index != -1:
                print(f"Deleting unused user '{user_name}'...")
                self.config['users'].pop(user_index)
        else:
            print(f"Info: User '{user_name}' is still in use by another context, not deleting.")

        if self.config.get('current-context') == context_name:
            print("Unsetting 'current-context' as it was deleted.")
            self.config['current-context'] = None
        return True

    def export_contexts(self, context_names: list[str]) -> dict | None:
        """
        Exports specified contexts and their related users and clusters into a new kubeconfig structure.

        Args:
            context_names (list[str]): A list of context names to export.

        Returns:
            dict | None: A dictionary representing a new, valid kubeconfig file,
                         or None if no valid contexts were found.
        """
        found_contexts = []
        cluster_names_to_include = set()
        user_names_to_include = set()

        for name in context_names:
            _, context_obj = find_item_by_name(self.config['contexts'], name)
            if context_obj:
                found_contexts.append(context_obj)
                cluster_names_to_include.add(context_obj['context']['cluster'])
                user_names_to_include.add(context_obj['context']['user'])
            else:
                print(f"Warning: Context '{name}' not found and will be skipped.", file=sys.stderr)

        if not found_contexts:
            print("Error: None of the specified contexts were found. No file will be created.", file=sys.stderr)
            return None

        # Filter clusters and users based on the names we collected
        found_clusters = [c for c in self.config['clusters'] if c['name'] in cluster_names_to_include]
        found_users = [u for u in self.config['users'] if u['name'] in user_names_to_include]

        # Assemble the new kubeconfig dictionary
        new_kubeconfig = {
            'apiVersion': 'v1',
            'kind': 'Config',
            'preferences': {},
            'current-context': found_contexts[0]['name'],  # Use the first valid context found
            'clusters': found_clusters,
            'users': found_users,
            'contexts': found_contexts,
        }
        return new_kubeconfig