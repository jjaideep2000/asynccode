#!/usr/bin/env python3
"""
Deploy Subscription Manager Lambda
Creates and deploys the centralized subscription management Lambda function
"""

import boto3
import json
import zipfile
import os
import tempfile
import shutil
import time
from datetime import datetime

def create_deployment_package():
    """Create deployment package for subscription manager Lambda"""
    
    print("=== CREATING SUBSCRIPTION MANAGER DEPLOYMENT PACKAGE ===")
    
    # Create temporary directory for package
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Working in temporary directory: {temp_dir}")
        
        # Copy handler file
        source_handler = "src/lambdas/subscription-manager/handler.py"
        dest_handler = os.path.join(temp_dir, "handler.py")
        
        if os.path.exists(source_handler):
            shutil.copy2(source_handler, dest_handler)
            print(f"✅ Copied {source_handler}")
        else:
            print(f"❌ Source handler not found: {source_handler}")
            return None
        
        # Copy requirements if they exist
        source_requirements = "src/lambdas/subscription-manager/requirements.txt"
        if os.path.exists(source_requirements):
            dest_requirements = os.path.join(temp_dir, "requirements.txt")
            shutil.copy2(source_requirements, dest_requirements)
            print(f"✅ Copied requirements.txt")
        
        # Create the zip file
        zip_path = "deploy/subscription-manager.zip"
        os.makedirs("deploy", exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zip_file.write(file_path, arc_name)
                    print(f"  Added: {arc_name}")
        
        print(f"✅ Created deployment package: {zip_path}")
        return zip_path

def deploy_lambda_function(zip_path):
    """Deploy or update the subscription manager Lambda function"""
    
    print("\n=== DEPLOYING SUBSCRIPTION MANAGER LAMBDA ===")
    
    lambda_client = boto3.client('lambda')
    iam_client = boto3.client('iam')
    
    function_name = "utility-customer-system-dev-subscription-manager"
    
    # Create IAM role for the Lambda function
    role_arn = create_lambda_role(iam_client)
    
    # Read the zip file
    with open(zip_path, 'rb') as zip_file:
        zip_content = zip_file.read()
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ Updated existing function: {function_name}")
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler="handler.lambda_handler",
            Runtime="python3.11",
            Timeout=300,  # 5 minutes
            MemorySize=512,
            Environment={
                'Variables': {
                    'MANAGED_FUNCTIONS': json.dumps([
                        {
                            "function_name": "utility-customer-system-dev-bank-account-setup",
                            "service_name": "bank-account-setup",
                            "description": "Bank account setup processing"
                        },
                        {
                            "function_name": "utility-customer-system-dev-payment-processing",
                            "service_name": "payment-processing", 
                            "description": "Payment processing"
                        }
                    ])
                }
            }
        )
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime="python3.11",
            Role=role_arn,
            Handler="handler.lambda_handler",
            Code={'ZipFile': zip_content},
            Description="Centralized subscription management for Lambda functions",
            Timeout=300,  # 5 minutes
            MemorySize=512,
            Environment={
                'Variables': {
                    'MANAGED_FUNCTIONS': json.dumps([
                        {
                            "function_name": "utility-customer-system-dev-bank-account-setup",
                            "service_name": "bank-account-setup",
                            "description": "Bank account setup processing"
                        },
                        {
                            "function_name": "utility-customer-system-dev-payment-processing",
                            "service_name": "payment-processing",
                            "description": "Payment processing"
                        }
                    ])
                }
            }
        )
        
        print(f"✅ Created new function: {function_name}")
    
    print(f"Function ARN: {response['FunctionArn']}")
    print(f"Last Modified: {response['LastModified']}")
    
    return response['FunctionArn']

def create_lambda_role(iam_client):
    """Create IAM role for the subscription manager Lambda"""
    
    role_name = "SubscriptionManagerLambdaRole"
    
    # Trust policy for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # Try to get existing role
        response = iam_client.get_role(RoleName=role_name)
        role_arn = response['Role']['Arn']
        print(f"✅ Using existing IAM role: {role_arn}")
        
    except iam_client.exceptions.NoSuchEntityException:
        # Create new role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="IAM role for subscription manager Lambda function"
        )
        
        role_arn = response['Role']['Arn']
        print(f"✅ Created new IAM role: {role_arn}")
        
        # Wait for role to propagate
        print("Waiting 10 seconds for IAM role to propagate...")
        time.sleep(10)
        
        # Attach basic Lambda execution policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        # Create and attach custom policy for Lambda management
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:ListEventSourceMappings",
                        "lambda:UpdateEventSourceMapping",
                        "lambda:GetEventSourceMapping"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        
        policy_name = "SubscriptionManagerPolicy"
        
        try:
            iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description="Policy for subscription manager Lambda to manage event source mappings"
            )
            
            # Get account ID for policy ARN
            sts_client = boto3.client('sts')
            account_id = sts_client.get_caller_identity()['Account']
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            
            print(f"✅ Created and attached custom policy: {policy_arn}")
            
        except iam_client.exceptions.EntityAlreadyExistsException:
            print(f"ℹ️  Policy {policy_name} already exists")
    
    return role_arn

def setup_sns_subscription(function_arn):
    """Set up SNS subscription for the subscription manager Lambda"""
    
    print("\n=== SETTING UP SNS SUBSCRIPTION ===")
    
    sns_client = boto3.client('sns')
    lambda_client = boto3.client('lambda')
    
    # SNS topic for subscription control
    topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
    
    try:
        # Subscribe Lambda to SNS topic
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='lambda',
            Endpoint=function_arn
        )
        
        subscription_arn = response['SubscriptionArn']
        print(f"✅ Created SNS subscription: {subscription_arn}")
        
        # Add permission for SNS to invoke Lambda
        try:
            lambda_client.add_permission(
                FunctionName=function_arn,
                StatementId='AllowSNSInvoke',
                Action='lambda:InvokeFunction',
                Principal='sns.amazonaws.com',
                SourceArn=topic_arn
            )
            print(f"✅ Added SNS invoke permission")
            
        except lambda_client.exceptions.ResourceConflictException:
            print(f"ℹ️  SNS invoke permission already exists")
        
    except Exception as e:
        print(f"❌ Error setting up SNS subscription: {e}")

def test_deployment():
    """Test the deployed subscription manager"""
    
    print("\n=== TESTING DEPLOYMENT ===")
    
    lambda_client = boto3.client('lambda')
    function_name = "utility-customer-system-dev-subscription-manager"
    
    # Test 1: Get status
    test_payload = {"action": "status"}
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"✅ Status test successful")
        print(f"Response: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Status test failed: {e}")

if __name__ == "__main__":
    print("Deploying Subscription Manager Lambda")
    print("=" * 60)
    
    # Create deployment package
    zip_path = create_deployment_package()
    
    if zip_path:
        # Deploy Lambda function
        function_arn = deploy_lambda_function(zip_path)
        
        # Set up SNS subscription
        setup_sns_subscription(function_arn)
        
        # Test deployment
        test_deployment()
        
        print("\n" + "=" * 60)
        print("✅ Subscription Manager deployment complete!")
        print(f"Function Name: utility-customer-system-dev-subscription-manager")
        print(f"Function ARN: {function_arn}")
        print("\nNext steps:")
        print("1. Remove subscription control logic from existing Lambda functions")
        print("2. Test centralized subscription management")
        print("3. Add new Lambda functions to MANAGED_FUNCTIONS configuration")
    else:
        print("❌ Deployment failed - could not create package")