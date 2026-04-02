"""
Setup verification script for ML training module.

This script checks if all required packages are installed.
"""

import sys

def check_package(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✓ {package_name} is installed")
        return True
    except ImportError:
        print(f"✗ {package_name} is NOT installed")
        return False

def main():
    """Check all required packages."""
    print("Checking ML Training module dependencies...")
    print("-" * 60)
    
    required_packages = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('scikit-learn', 'sklearn'),
    ]
    
    all_installed = True
    for package_name, import_name in required_packages:
        if not check_package(package_name, import_name):
            all_installed = False
    
    print("-" * 60)
    
    if all_installed:
        print("\n✓ All required packages are installed!")
        print("You can proceed with data collection and preprocessing.")
    else:
        print("\n✗ Some packages are missing!")
        print("Please install them using:")
        print("  pip install pandas numpy scikit-learn")
        print("\nOr install all requirements:")
        print("  pip install -r requirements.txt")
    
    return all_installed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

