print("Testing Python environment...")

try:
    import django
    print(f"Django version: {django.VERSION}")
except ImportError:
    print("Django not installed")

try:
    import rest_framework
    print("Django REST Framework installed")
except ImportError:
    print("Django REST Framework not installed")

try:
    import dotenv
    print("python-dotenv installed")
except ImportError:
    print("python-dotenv not installed")

print("\nTest complete!")
