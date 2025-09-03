#!/usr/bin/env python3
"""
Deploy NEW Lambda function with observability
This creates a separate Lambda function for observability demo
Does NOT modify existing working Lambda functions
"""

import boto3
import json
import zipfile
import os
import time
from datetime import datetime

# Configuration for NEW observability Lambda
LAMBDA_FUNCTION_NAME = "utility-customer-system-dev-bank-account-observability"
LAMBDA_ROLE_ARN = "arn:aws:iam::088153174619:role/lambda-exec-role"
QUEUE_ARN = "arn:aws:sqs:us-east-2:088153174619:utility-customer-system-dev-bank-account-setup.fifo"

def create_lambda_package():
    """Create deployment package for observability Lambda"""
    
    print("Creating Lambda deployment package...")
    
    # Create package directory
    package_dir = "lambda_package_observability"
    os.makedirs(package_dir, exist_ok=True)
    
    # Copy observability files
    import shutil
    
    # Copy the instrumented Lambda function
    shutil.copy2("lambda_functions/bank_account_instrumented.py", 
                 f"{package_dir}/lambda_function.py")
    
    # Copy observability config
    os.makedirs(f"{package_dir}/observability", exist_ok=True)
    shutil.copy2("observability/otel_config.py", 
                 f"{package_dir}/observability/otel_config.py")
    
    # Create __init__.py files
    with open(f"{package_dir}/observability/__init__.py", 'w') as f:
        f.write("")
    
    # Create zip file
    zip_filename = "observability_lambda.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    # Cleanup
    shutil.rmtree(package_dir)
    
    print(f"Created deployment package: {zip_filename}")
    return zip_filename

def deploy_observability_lambda():
    """Deploy the new observability Lambda function"""
    
    print(f"Deploying NEW observability Lambda function...")
    print(f"Function name: {LAMBDA_FUNCTION_NAME}")
    print(f"This will NOT modify existing Lambda functions")
    print("-" * 60)
    
    lambda_client = boto3.client('lambda')
    
    # Create deployment package
    zip_filename = create_lambda_package()
    
    try:
        # Read the zip file
        with open(zip_filename, 'rb') as f:
            zip_content = f.read()
        
        # Check if function exists
        try:
            lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
            function_exists = True
            print(f"Function {LAMBDA_FUNCTION_NAME} already exists - updating...")
        except lambda_client.exceptions.ResourceNotFoundException:
            function_exists = False
            print(f"Creating new function {LAMBDA_FUNCTION_NAME}...")
        
        if function_exists:
            # Update existing function
            response = lambda_client.update_function_code(
                FunctionName=LAMBDA_FUNCTION_NAME,
                ZipFile=zip_content
            )
            print(f"Updated function code")
            
            # Update configuration
            lambda_client.update_function_configuration(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Runtime='python3.9',
                Handler='lambda_function.lambda_handler',
                Timeout=30,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'ENVIRONMENT': 'dev',
                        'OBSERVABILITY_ENABLED': 'true'
                    }
                }
            )
            print(f"Updated function configuration")
            
        else:
            # Create new function
            response = lambda_client.create_function(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Runtime='python3.9',
                Role=LAMBDA_ROLE_ARN,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='Bank Account Setup with OpenTelemetry Observability (Demo)',
                Timeout=30,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'ENVIRONMENT': 'dev',
                        'OBSERVABILITY_ENABLED': 'true'
                    }
                },
                Tags={
                    'Project': 'utility-customer-system',
                    'Environment': 'dev',
                    'Component': 'observability-demo'
                }
            )
            print(f"Created new function: {response['FunctionArn']}")
        
        # Wait for function to be ready
        print("Waiting for function to be ready...")
        waiter = lambda_client.get_waiter('function_active')
        waiter.wait(FunctionName=LAMBDA_FUNCTION_NAME)
        
        return True
        
    except Exception as e:
        print(f"Error deploying Lambda: {e}")
        return False
    
    finally:
        # Cleanup zip file
        if os.path.exists(zip_filename):
            os.remove(zip_filename)

def create_separate_sqs_trigger():
    """Create a separate SQS queue for observability demo"""
    
    print("\nCreating separate SQS queue for observability demo...")
    
    sqs = boto3.client('sqs')
    
    # Create observability demo queue
    queue_name = "utility-customer-system-dev-bank-account-observability.fifo"
    
    try:
        # Check if queue exists
        try:
            response = sqs.get_queue_url(QueueName=queue_name)
            queue_url = response['QueueUrl']
            print(f"Queue already exists: {queue_url}")
        except sqs.exceptions.QueueDoesNotExist:
            # Create new queue
            response = sqs.create_queue(
                QueueName=queue_name,
                Attributes={
                    'FifoQueue': 'true',
                    'ContentBasedDeduplication': 'true',
                    'VisibilityTimeout': '30',
                    'MessageRetentionPeriod': '1209600',  # 14 days
                    'ReceiveMessageWaitTimeSeconds': '0'
                }
            )
            queue_url = response['QueueUrl']
            print(f"Created new queue: {queue_url}")
        
        # Get queue ARN
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )
        queue_arn = attrs['Attributes']['QueueArn']
        
        return queue_url, queue_arn
        
    except Exception as e:
        print(f"Error creating SQS queue: {e}")
        return None, None

def setup_lambda_trigger(queue_arn):
    """Setup SQS trigger for the observability Lambda"""
    
    print(f"\nSetting up SQS trigger for observability Lambda...")
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Create event source mapping
        response = lambda_client.create_event_source_mapping(
            EventSourceArn=queue_arn,
            FunctionName=LAMBDA_FUNCTION_NAME,
            BatchSize=1,
            MaximumBatchingWindowInSeconds=0,
            Enabled=True
        )
        
        print(f"Created event source mapping: {response['UUID']}")
        return response['UUID']
        
    except lambda_client.exceptions.ResourceConflictException:
        print("Event source mapping already exists")
        
        # List existing mappings
        mappings = lambda_client.list_event_source_mappings(
            FunctionName=LAMBDA_FUNCTION_NAME
        )
        
        for mapping in mappings['EventSourceMappings']:
            if mapping['EventSourceArn'] == queue_arn:
                print(f"Found existing mapping: {mapping['UUID']}")
                return mapping['UUID']
        
        return None
        
    except Exception as e:
        print(f"Error setting up trigger: {e}")
        return None

def create_sns_subscription(queue_arn, queue_url):
    """Create SNS subscription for the observability queue"""
    
    print(f"\nCreating SNS subscription for observability queue...")
    
    sns = boto3.client('sns')
    
    topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
    
    try:
        # Subscribe queue to SNS topic
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='sqs',
            Endpoint=queue_arn,
            Attributes={
                'FilterPolicy': json.dumps({
                    'observability_demo': ['true']
                }),
                'RawMessageDelivery': 'true'
            }
        )
        
        subscription_arn = response['SubscriptionArn']
        print(f"Created SNS subscription: {subscription_arn}")
        
        # Set queue policy to allow SNS
        sqs = boto3.client('sqs')
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "sns.amazonaws.com"},
                    "Action": "sqs:SendMessage",
                    "Resource": queue_arn,
                    "Condition": {
                        "ArnEquals": {
                            "aws:SourceArn": topic_arn
                        }
                    }
                }
            ]
        }
        
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={
                'Policy': json.dumps(policy)
            }
        )
        
        print("Set queue policy for SNS access")
        return subscription_arn
        
    except Exception as e:
        print(f"Error creating SNS subscription: {e}")
        return None

def main():
    """Main deployment function"""
    
    print("DEPLOYING OBSERVABILITY LAMBDA (NEW FUNCTION)")
    print("This creates a separate Lambda for observability demo")
    print("Your existing Lambda functions will NOT be modified")
    print("=" * 70)
    
    # Step 1: Deploy Lambda function
    if not deploy_observability_lambda():
        print("Failed to deploy Lambda function")
        return
    
    # Step 2: Create separate SQS queue
    queue_url, queue_arn = create_separate_sqs_trigger()
    if not queue_arn:
        print("Failed to create SQS queue")
        return
    
    # Step 3: Setup Lambda trigger
    mapping_uuid = setup_lambda_trigger(queue_arn)
    if not mapping_uuid:
        print("Warning: Could not setup Lambda trigger")
    
    # Step 4: Create SNS subscription
    subscription_arn = create_sns_subscription(queue_arn, queue_url)
    if not subscription_arn:
        print("Warning: Could not create SNS subscription")
    
    print(f"\nOBSERVABILITY LAMBDA DEPLOYMENT COMPLETE!")
    print(f"=" * 50)
    print(f"New Lambda Function: {LAMBDA_FUNCTION_NAME}")
    print(f"New SQS Queue: {queue_url}")
    print(f"Event Source Mapping: {mapping_uuid}")
    print(f"SNS Subscription: {subscription_arn}")
    print(f"\nTo test observability:")
    print(f"1. Run: python3 demo_observability_bank_account.py")
    print(f"2. Check CloudWatch logs: /aws/lambda/{LAMBDA_FUNCTION_NAME}")
    print(f"3. Your existing Lambda functions remain unchanged")

if __name__ == "__main__":
    main()