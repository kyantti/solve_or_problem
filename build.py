#!/usr/bin/env python3
"""
Build and publish script for solve-or-problem package.
"""

import subprocess
import sys
from pathlib import Path


from typing import Optional


def run_command(command: str, description: Optional[str] = None):
    """Run a shell command and handle errors."""
    if description:
        print(f"\n{description}...")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error output: {result.stderr}")
        sys.exit(1)
    
    print(result.stdout)
    return result


def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    # Remove build directories
    for pattern in ["build", "dist", "*.egg-info"]:
        run_command(f"rm -rf {pattern}", f"Removing {pattern}")


def build_package():
    """Build the package."""
    print("📦 Building package...")
    run_command("python -m build", "Building wheel and source distribution")


def check_package():
    """Check the built package."""
    print("🔍 Checking package...")
    run_command("twine check dist/*", "Checking package integrity")


def install_local():
    """Install package locally for testing."""
    print("🔧 Installing package locally...")
    run_command("pip install -e .", "Installing in development mode")


def test_package():
    """Run tests."""
    print("🧪 Running tests...")
    run_command("python -m pytest tests/ -v", "Running test suite")


def publish_test():
    """Publish to test PyPI."""
    print("🚀 Publishing to test PyPI...")
    run_command(
        "twine upload --repository testpypi dist/*",
        "Uploading to test PyPI"
    )


def publish_prod():
    """Publish to production PyPI."""
    print("🚀 Publishing to production PyPI...")
    run_command("twine upload dist/*", "Uploading to production PyPI")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("""
Usage: python build.py <command>

Commands:
  clean      - Clean build artifacts
  build      - Build the package
  check      - Check the built package
  install    - Install locally for testing
  test       - Run tests
  test-pypi  - Publish to test PyPI
  publish    - Publish to production PyPI
  all        - Clean, build, check, and test
        """)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "clean":
        clean_build()
    elif command == "build":
        build_package()
    elif command == "check":
        check_package()
    elif command == "install":
        install_local()
    elif command == "test":
        test_package()
    elif command == "test-pypi":
        publish_test()
    elif command == "publish":
        publish_prod()
    elif command == "all":
        clean_build()
        build_package()
        check_package()
        install_local()
        test_package()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
