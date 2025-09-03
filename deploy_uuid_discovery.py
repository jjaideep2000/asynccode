#!/usr/bin/env python3
"""
Deploy script to update Lambda functions with dynamic UUID discovery
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def run_command(command, cwd=None):
 """Run a shell command and return the result"""
 print(f"Running: {command}")
 
 try:
 result = subprocess.run(
 command, 
 shell=True, 
 cwd=cwd,
 capture_output=True, 
 text=True, 
 check=True
 )
 
 if result.stdout:
 print(f"Output: {result.stdout.strip()}")
 
 return result
 
 except subprocess.CalledProcessError as e:
 print(f"Error: {e}")
 if e.stdout:
 print(f"Stdout: {e.stdout}")
 if e.stderr:
 print(f"Stderr: {e.stderr}")
 raise

def package_lambda(lambda_dir, output_dir):
 """Package a Lambda function"""
 
 lambda_name = os.path.basename(lambda_dir)
 zip_file = os.path.join(output_dir, f"{lambda_name}.zip")
 
 print(f"\nPackaging {lambda_name}")
 print("-" * 40)
 
 # Create output directory
 os.makedirs(output_dir, exist_ok=True)
 
 # Remove existing zip file
 if os.path.exists(zip_file):
 os.remove(zip_file)
 
 # Create zip file with Lambda code and shared modules
 commands = [
 f"cd {lambda_dir} && zip -r {os.path.abspath(zip_file)} .",
 f"cd src/shared && zip -r {os.path.abspath(zip_file)} . -x '__pycache__/*'"
 ]
 
 for cmd in commands:
 run_command(cmd)
 
 print(f"Created: {zip_file}")
 return zip_file

def update_lambda_function(function_name, zip_file):
 """Update Lambda function code"""
 
 print(f"\nUpdating Lambda function: {function_name}")
 print("-" * 50)
 
 # Update function code
 cmd = f"aws lambda update-function-code --function-name {function_name} --zip-file fileb://{zip_file} --output json"
 run_command(cmd)
 
 # Wait for update to complete
 print("Waiting for update to complete...")
 time.sleep(5)
 
 # Get function info
 cmd = f"aws lambda get-function --function-name {function_name} --output json"
 result = run_command(cmd)
 
 function_info = json.loads(result.stdout)
 print(f"Function updated: {function_info['Configuration']['LastModified']}")

def deploy_all_functions():
 """Deploy all Lambda functions with dynamic UUID discovery"""
 
 print("Deploying Lambda Functions with Dynamic UUID Discovery")
 print("=" * 60)
 
 # Lambda functions to deploy
 lambdas = [
 {
 'dir': 'src/lambdas/bank-account',
 'function_name': 'utility-customer-system-dev-bank-account-setup'
 },
 {
 'dir': 'src/lambdas/payment', 
 'function_name': 'utility-customer-system-dev-payment-processing'
 }
 ]
 
 output_dir = "deploy/packages"
 
 for lambda_config in lambdas:
 try:
 # Package Lambda
 zip_file = package_lambda(lambda_config['dir'], output_dir)
 
 # Update function
 update_lambda_function(lambda_config['function_name'], zip_file)
 
 except Exception as e:
 print(f"Failed to deploy {lambda_config['function_name']}: {e}")
 continue
 
 print("\n" + "=" * 60)
 print("Deployment Complete!")

def test_deployed_functions():
 """Test the deployed functions"""
 
 print("\n🧪 Testing Deployed Functions")
 print("=" * 40)
 
 # Test messages
 test_messages = [
 {
 'function': 'utility-customer-system-dev-bank-account-setup',
 'payload': {
 'customer_id': 'test-customer-001',
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': 'test-msg-001'
 }
 },
 {
 'function': 'utility-customer-system-dev-payment-processing',
 'payload': {
 'customer_id': 'test-customer-002', 
 'amount': 150.00,
 'payment_method': 'bank_account',
 'message_id': 'test-msg-002'
 }
 }
 ]
 
 for test in test_messages:
 print(f"\nTesting: {test['function']}")
 print("-" * 30)
 
 try:
 # Create payload file
 payload_file = f"/tmp/test_payload_{int(time.time())}.json"
 with open(payload_file, 'w') as f:
 json.dump(test['payload'], f)
 
 # Invoke function
 cmd = f"aws lambda invoke --function-name {test['function']} --payload fileb://{payload_file} /tmp/response.json --output json"
 run_command(cmd)
 
 # Read response
 with open('/tmp/response.json', 'r') as f:
 response = json.load(f)
 
 print(f"Response: {json.dumps(response, indent=2)}")
 
 # Cleanup
 os.remove(payload_file)
 
 except Exception as e:
 print(f"Test failed: {e}")

if __name__ == "__main__":
 print("Starting Lambda Deployment with Dynamic UUID Discovery")
 
 try:
 deploy_all_functions()
 
 # Ask if user wants to test
 response = input("\n🤔 Would you like to test the deployed functions? (y/n): ")
 if response.lower() in ['y', 'yes']:
 test_deployed_functions()
 
 except KeyboardInterrupt:
 print("\nDeployment cancelled by user")
 except Exception as e:
 print(f"\nDeployment failed: {e}")
 sys.exit(1)
 
 print("\nAll done!")