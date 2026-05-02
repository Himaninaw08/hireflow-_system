import os
from pathlib import Path

print("Setting up directories...")

BASE_DIR = Path(__file__).resolve().parent
print(f"Base directory: {BASE_DIR}")

# Create directories
dirs_to_create = ['static', 'media', 'staticfiles']

for dir_name in dirs_to_create:
    dir_path = BASE_DIR / dir_name
    try:
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Created/Verified: {dir_name}")
    except Exception as e:
        print(f"❌ Error creating {dir_name}: {e}")

# Verify directories exist
print("\n📁 Directory verification:")
for dir_name in dirs_to_create:
    dir_path = BASE_DIR / dir_name
    exists = dir_path.exists()
    print(f"{'✅' if exists else '❌'} {dir_name}: {'Exists' if exists else 'Missing'}")

# List all items in current directory
print("\n📋 Current directory contents:")
try:
    items = list(BASE_DIR.iterdir())
    for item in sorted(items):
        if item.is_dir():
            print(f"📁 {item.name}/")
        else:
            print(f"📄 {item.name}")
except Exception as e:
    print(f"Error listing directory: {e}")

print("\n✅ Directory setup complete!")
