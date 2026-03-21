#!/usr/bin/env python
"""Create directory structure for the project."""
import os

base_path = os.path.dirname(os.path.abspath(__file__))

directories = [
    'app',
    'app\\core',
    'app\\db',
    'app\\models',
    'app\\schemas',
    'app\\services',
    'app\\routes',
    'app\\templates',
    'app\\static\\css',
    'app\\static\\js',
    'alembic',
    'alembic\\versions'
]

for directory in directories:
    full_path = os.path.join(base_path, directory)
    os.makedirs(full_path, exist_ok=True)
    print(f'✓ Created: {directory}')

print('\n✓ Directory structure created successfully!')
