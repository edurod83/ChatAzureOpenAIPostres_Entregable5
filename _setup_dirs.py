"""
Directory setup script for ChatAzureOpenAIPostres project.
Creates all necessary subdirectories using os.makedirs.
"""

import os
import sys

# Base path where this script is located
base_path = os.path.dirname(os.path.abspath(__file__))

# List of directories to create
directories = [
    "app",
    "app\\core",
    "app\\db",
    "app\\models",
    "app\\schemas",
    "app\\services",
    "app\\routes",
    "app\\templates",
    "app\\static\\css",
    "app\\static\\js",
    "alembic",
    "alembic\\versions",
]

def create_directories():
    """Create all required directories."""
    print(f"Base path: {base_path}")
    print(f"Creating {len(directories)} directories...\n")
    
    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            print(f"✓ Created: {dir_path}")
        except Exception as e:
            print(f"✗ Failed to create {dir_path}: {e}")
            return False
    
    print(f"\n✓ All directories created successfully!")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
