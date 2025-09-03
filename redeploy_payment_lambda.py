#!/usr/bin/env python3
"""
Redeploy Payment Lambda with Correct Handler
The deployment package might be corrupted or missing the handler file
"""

import boto3
import json
import zipfile
import os
import tempfile

def check_deployment_package():
    """Check what's in the current deployment package"""
    
    print("=== CHECKING DEPLOYMENT PACKAGE ===")
    
    zip_path = "deploy/payment-processing.zip"
    
    if os.path.exists(zip_path):
        print(f"Found deployment package: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                print(f"Files in package ({len(file_list)}):")
                
                for file_name in sorted(file_list):
                    print(f"  {file_name}")
                    
                # Check if handler.py exists
                if 'handler.py' in file_list:
                    print("✅ handler.py found in package")
                else:
                    print("❌ handler.py NOT found in package")
                    
                # Check if lambda_function.py exists (wrong file)
                if 'lambda_function.py' in file_list:
                    print("⚠️  lambda_function.py found (this might be causing confusion)")
                    
        except Exception as e:
            print(f"Error reading zip file: {e}")
    else:
        print(f"❌ Deployment package not found: {zip_path}")

def create_new_deployment_package():
    """Create a new deployment package with the correct structure"""
    
    print("\n=== CREATING NEW DEPLOYMENT PACKAGE ===")
    
    # Create a temporary directory for the package
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Working in temporary directory: {temp_dir}")
        
        # Copy the handler file
        import shutil
        
        source_handler = "src/lambdas/payment/handler.py"
        dest_handler = os.path.join(temp_dir, "handler.py")
        
        if os.path.exists(source_handler):
            shutil.copy2(source_handler, dest_handler)
            print(f"✅ Copied {source_handler} to package")
        else:
            print(f"❌ Source handler not found: {source_handler}")
            return None
            
        # Copy requirements if they exist
        source_requirements = "src/lambdas/payment/requirements.txt"
        if os.path.exists(source_requirements):
            dest_requirements = os.path.join(temp_dir, "requirements.txt")
            shutil.copy2(source_requirements, dest_requirements)
            print(f"✅ Copied requirements.txt")
            
        # Copy shared modules
        shared_dir = "src/shared"
        if os.path.exists(shared_dir):
            dest_shared = os.path.join(temp_dir, "shared")
            shutil.copytree(shared_dir, dest_shared)
            print(f"✅ Copied shared modules")
            
        # Create the zip file
        zip_path = "deploy/payment-processing-fixed.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zip_file.write(file_path, arc_name)
                    print(f"  Added: {arc_name}")
                    
        print(f"✅ Created new deployment package: {zip_path}")
        return zip_path

def deploy_fixed_lambda(zip_path):
    """Deploy the fixed Lambda function"""
    
    print(f"\n=== DEPLOYING FIXED LAMBDA ===")
    
    lambda_client = boto3.client('lambda')
    function_name = "utility-customer-system-dev-payment-processing"
    
    try:
        # Read the zip file
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
            
        print(f"Uploading {len(zip_content)} bytes...")
        
        # Update the function code
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print("✅ Function code updated successfully!")
        print(f"Code SHA256: {response['CodeSha256']}")
        print(f"Last Modified: {response['LastModified']}")
        
        # Ensure the handler is correct
        config_response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler="handler.lambda_handler"
        )
        
        print(f"✅ Handler set to: {config_response['Handler']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error deploying function: {e}")
        return False

def test_deployed_function():
    """Test the newly deployed function"""
    
    print(f"\n=== TESTING DEPLOYED FUNCTION ===")
    
    lambda_client = boto3.client('lambda')
    function_name = "utility-customer-system-dev-payment-processing"
    
    test_payload = {
        "customer_id": "test-customer-deployed-123",
        "amount": 75.00,
        "payment_method": "bank_account",
        "message_id": "test-deployed-message-123"
    }
    
    try:
        print("Testing deployed Lambda function...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"Status Code: {status_code}")
        print(f"Response: {json.dumps(payload, indent=2)}")
        
        if status_code == 200 and 'errorMessage' not in payload:
            print("✅ Lambda function is now working correctly!")
            return True
        else:
            print("❌ Lambda function still has issues")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        return False

if __name__ == "__main__":
    print("Redeploying Payment Lambda with Correct Handler")
    print("=" * 60)
    
    # Check current package
    check_deployment_package()
    
    # Create new package
    new_zip_path = create_new_deployment_package()
    
    if new_zip_path:
        # Deploy the fixed function
        if deploy_fixed_lambda(new_zip_path):
            # Test the deployment
            if test_deployed_function():
                print("\n✅ SUCCESS: Payment Lambda is now working!")
                print("The stuck messages should be processed automatically.")
            else:
                print("\n❌ FAILED: Lambda still has issues after deployment")
        else:
            print("\n❌ FAILED: Could not deploy the fixed Lambda")
    else:
        print("\n❌ FAILED: Could not create deployment package")
    
    print("\n" + "=" * 60)
    print("Redeployment complete!")