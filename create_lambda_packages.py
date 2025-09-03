#!/usr/bin/env python3
"""
Create proper Lambda deployment packages with shared modules
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

def create_lambda_package(lambda_name, lambda_dir, shared_dir, output_file):
 """Create a Lambda deployment package with shared modules"""
 
 print(f"\nCreating package for {lambda_name}")
 print("-" * 40)
 
 # Create temporary directory for packaging
 with tempfile.TemporaryDirectory() as temp_dir:
 print(f"Using temp directory: {temp_dir}")
 
 # Copy Lambda function files
 lambda_src = Path(lambda_dir)
 for file in lambda_src.glob("*"):
 if file.is_file() and not file.name.startswith('.'):
 dest = Path(temp_dir) / file.name
 shutil.copy2(file, dest)
 print(f" Copied: {file.name}")
 
 # Copy shared modules
 shared_src = Path(shared_dir)
 shared_dest = Path(temp_dir) / "shared"
 shutil.copytree(shared_src, shared_dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
 print(f" Copied shared modules to: shared/")
 
 # List contents for verification
 print(f" Package contents:")
 for item in Path(temp_dir).rglob("*"):
 if item.is_file():
 rel_path = item.relative_to(temp_dir)
 print(f" {rel_path}")
 
 # Create zip file
 output_path = Path(output_file)
 output_path.parent.mkdir(parents=True, exist_ok=True)
 
 # Remove existing file
 if output_path.exists():
 output_path.unlink()
 
 # Create zip
 shutil.make_archive(str(output_path.with_suffix('')), 'zip', temp_dir)
 
 print(f" Created: {output_path}")
 
 # Verify zip contents
 result = subprocess.run(['unzip', '-l', str(output_path)], 
 capture_output=True, text=True)
 if result.returncode == 0:
 print(f" Zip contents verified:")
 for line in result.stdout.split('\n')[3:-3]: # Skip header and footer
 if line.strip():
 print(f" {line.strip()}")
 
 return output_path

def main():
 """Create all Lambda packages"""
 
 print("Creating Lambda Deployment Packages with Shared Modules")
 print("=" * 60)
 
 # Configuration
 packages = [
 {
 'name': 'bank-account-setup',
 'lambda_dir': 'src/lambdas/bank-account',
 'output_file': 'deploy/bank-account-setup.zip'
 },
 {
 'name': 'payment-processing', 
 'lambda_dir': 'src/lambdas/payment',
 'output_file': 'deploy/payment-processing.zip'
 }
 ]
 
 shared_dir = 'src/shared'
 
 # Verify source directories exist
 if not Path(shared_dir).exists():
 print(f"Shared directory not found: {shared_dir}")
 return False
 
 created_packages = []
 
 for package in packages:
 lambda_dir = package['lambda_dir']
 
 if not Path(lambda_dir).exists():
 print(f"Lambda directory not found: {lambda_dir}")
 continue
 
 try:
 output_path = create_lambda_package(
 package['name'],
 lambda_dir,
 shared_dir,
 package['output_file']
 )
 created_packages.append(output_path)
 
 except Exception as e:
 print(f"Failed to create package for {package['name']}: {e}")
 
 # Summary
 print(f"\nPackage Creation Summary")
 print("=" * 30)
 print(f"Created {len(created_packages)} packages:")
 
 for package_path in created_packages:
 size = package_path.stat().st_size / 1024 # KB
 print(f" {package_path.name}: {size:.1f} KB")
 
 print(f"\nNext Steps:")
 print(f" 1. Deploy with: cd terraform && terraform apply")
 print(f" 2. Test the updated Lambda functions")
 print(f" 3. Verify dynamic UUID discovery is working")
 
 return len(created_packages) == len(packages)

if __name__ == "__main__":
 success = main()
 if not success:
 exit(1)
 print("\nAll packages created successfully!")