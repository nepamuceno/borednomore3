"""
File Manager - COMPLETE WORKING VERSION
"""

import os
import json
import yaml

class FileManager:
    def __init__(self):
        pass
    
    def read_file(self, file_path):
        """Read file content"""
        try:
            if not os.path.exists(file_path):
                return ""
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""
    
    def write_file(self, file_path, content):
        """Write content to file"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file {file_path}: {e}")
            return False
    
    def load_json(self, file_path):
        """Load JSON file"""
        try:
            if not os.path.exists(file_path):
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON {file_path}: {e}")
            return {}
    
    def save_json(self, file_path, data):
        """Save data to JSON file"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving JSON {file_path}: {e}")
            return False
    
    def load_yaml(self, file_path):
        """Load YAML file"""
        try:
            if not os.path.exists(file_path):
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading YAML {file_path}: {e}")
            return {}
    
    def get_file_info(self, file_path):
        """Get file information"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'extension': os.path.splitext(file_path)[1],
                'name': os.path.basename(file_path),
                'directory': os.path.dirname(file_path)
            }
        except Exception as e:
            print(f"Error getting file info for {file_path}: {e}")
            return None
    
    def list_directory(self, directory_path, recursive=False):
        """List directory contents"""
        try:
            if not os.path.exists(directory_path):
                return []
            
            files = []
            if recursive:
                for root, dirs, filenames in os.walk(directory_path):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
            else:
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isfile(item_path):
                        files.append(item_path)
            
            return files
        except Exception as e:
            print(f"Error listing directory {directory_path}: {e}")
            return []
