import os
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Create directories
directories = [
    'static',
    'media', 
    'staticfiles'
]

for dir_name in directories:
    dir_path = BASE_DIR / dir_name
    dir_path.mkdir(exist_ok=True)
    print(f"Directory '{dir_name}' created at: {dir_path}")
    print(f"Exists: {dir_path.exists()}")

# List all directories
print("\nCurrent directories:")
for item in BASE_DIR.iterdir():
    if item.is_dir():
        print(f"📁 {item.name}")
    else:
        print(f"📄 {item.name}")
