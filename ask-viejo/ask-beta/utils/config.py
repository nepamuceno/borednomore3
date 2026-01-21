"""
Configuration - COMPLETE WORKING VERSION
"""

APP_CONFIG = {
    'default_appearance': 'dark',
    'default_color_theme': 'blue',
    'window_geometry': '1280x850',
    'window_min_size': (1000, 750),
    'auto_save_interval': 300000,  # 5 minutes in milliseconds
    'max_history_entries': 100,
    'supported_file_types': [
        ('Text files', '*.txt'),
        ('Markdown files', '*.md'),
        ('Python files', '*.py'),
        ('JSON files', '*.json'),
        ('YAML files', '*.yaml *.yml'),
        ('All files', '*.*')
    ]
}
