import os
import json
import importlib
import sys

class TransitionManager:
    """
    The Brain of the Transition Engine.
    Handles dynamic discovery of categories and automated instantiation.
    """
    def __init__(self, categories_dir="categories"):
        # Set absolute path to the package directory to ensure files are found
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.categories_path = os.path.join(self.base_path, categories_dir)
        self.catalog = {}

    def scan_transitions(self):
        """
        Scans all subdirectories in 'categories' for meta.json files.
        Fills the catalog with metadata for GUI use.
        """
        if not os.path.exists(self.categories_path):
            print(f"Error: Categories directory not found at {self.categories_path}")
            return {}

        for category_folder in os.listdir(self.categories_path):
            folder_path = os.path.join(self.categories_path, category_folder)
            
            if os.path.isdir(folder_path):
                meta_file = os.path.join(folder_path, "meta.json")
                
                if os.path.exists(meta_file):
                    try:
                        with open(meta_file, 'r') as f:
                            data = json.load(f)
                            # Key the catalog by the folder name or category_id
                            cat_id = data.get('category_id', category_folder)
                            self.catalog[cat_id] = data
                    except Exception as e:
                        print(f"Error loading metadata for {category_folder}: {e}")
        
        return self.catalog

    def get_transition_instance(self, category_id):
        """
        Dynamically imports the engine.py from the specified category
        and returns an instance of the transition class found inside.
        """
        try:
            # Construct the module path for importlib
            module_name = f"bnm3_transitions.categories.{category_id}.engine"
            
            # Ensure the module is loaded/reloaded
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
            
            # SEARCH LOGIC: Look for any class ending in 'Transition' 
            # that is NOT the base 'Transition' class itself.
            for attr_name in dir(module):
                if attr_name.endswith("Transition") and attr_name != "Transition":
                    transition_class = getattr(module, attr_name)
                    return transition_class()
            
            raise AttributeError(f"No valid Transition class found in {module_name}")

        except ImportError as e:
            print(f"Critical Error: Could not find engine for '{category_id}'. {e}")
            return None
        except Exception as e:
            print(f"Error instantiating transition '{category_id}': {e}")
            return None

    def get_metadata(self, category_id):
        """Helper for the GUI to fetch specific info."""
        return self.catalog.get(category_id, {})
