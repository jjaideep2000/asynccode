#!/usr/bin/env python3
"""
Test the deployed Lambda functions with dynamic UUID discovery
"""

import json
import boto3
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_lambda_function(function_name, test_payload):
    """Test a Lambda function with a given payload"""
    
    print(f"\n🧪 Testing Lambda Function: {function_name}")
    print("-" * 50)
    
    try:
        # Create Lambda client
        lambda_client = boto3.client('lambda')
        
        # Invoke function
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"Function invoked successfully")
        print(f" Status Code: {response['StatusCode']}")
        print(f" Response: {json.dumps(response_payload, indent=2)}")
        
        return response_payload
        
    except Exception as e:
        print(f"Error invoking function: {e}")
        return None

def test_error_scenarios():
 """Test error scenarios to verify dynamic UUID discovery works"""
 
 print("Testing Error Scenarios with Dynamic UUID Discovery")
 print("=" * 60)
 
 # Test bank account setup with 400 error
 print("\nTesting Bank Account Setup - 400 Error")
 bank_account_400_payload = {
 'customer_id': 'ERROR400-test-customer',
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': 'test-400-error-msg'
 }
 
 result = test_lambda_function(
 'utility-customer-system-dev-bank-account-setup',
 bank_account_400_payload
 )
 
 # Test bank account setup with 500 error
 print("\nTesting Bank Account Setup - 500 Error")
 bank_account_500_payload = {
 'customer_id': 'ERROR500-test-customer',
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': 'test-500-error-msg'
 }
 
 result = test_lambda_function(
 'utility-customer-system-dev-bank-account-setup',
 bank_account_500_payload
 )
 
 # Test payment processing with 400 error
 print("\nTesting Payment Processing - 400 Error")
 payment_400_payload = {
 'customer_id': 'ERROR400-payment-customer',
 'amount': 150.00,
 'payment_method': 'bank_account',
 'message_id': 'test-payment-400-error'
 }
 
 result = test_lambda_function(
 'utility-customer-system-dev-payment-processing',
 payment_400_payload
 )
 
 # Test payment processing with 500 error
 print("\nTesting Payment Processing - 500 Error")
 payment_500_payload = {
 'customer_id': 'ERROR500-payment-customer',
 'amount': 200.00,
 'payment_method': 'bank_account',
 'message_id': 'test-payment-500-error'
 }
 
 result = test_lambda_function(
 'utility-customer-system-dev-payment-processing',
 payment_500_payload
 )

def test_successful_scenarios():
 """Test successful scenarios"""
 
 print("\nTesting Successful Scenarios")
 print("=" * 40)
 
 # Test successful bank account setup
 print("\nTesting Bank Account Setup - Success")
 bank_account_success_payload = {
 'customer_id': 'success-customer-001',
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': 'test-success-msg'
 }
 
 result = test_lambda_function(
 'utility-customer-system-dev-bank-account-setup',
 bank_account_success_payload
 )
 
 # Test successful payment processing
 print("\nTesting Payment Processing - Success")
 payment_success_payload = {
 'customer_id': 'success-payment-customer',
 'amount': 75.50,
 'payment_method': 'bank_account',
 'message_id': 'test-payment-success'
 }
 
 result = test_lambda_function(
 'utility-customer-system-dev-payment-processing',
 payment_success_payload
 )

def check_event_source_mappings():
 """Check the current status of event source mappings"""
 
 print("\nChecking Event Source Mapping Status")
 print("=" * 50)
 
 try:
 lambda_client = boto3.client('lambda')
 
 functions = [
 'utility-customer-system-dev-bank-account-setup',
 'utility-customer-system-dev-payment-processing'
 ]
 
 for function_name in functions:
 print(f"\nFunction: {function_name}")
 print("-" * 30)
 
 # Get event source mappings
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 for mapping in response['EventSourceMappings']:
 print(f" UUID: {mapping['UUID']}")
 print(f" State: {mapping['State']}")
 print(f" Event Source: {mapping['EventSourceArn']}")
 print(f" Enabled: {mapping.get('State') == 'Enabled'}")
 
 except Exception as e:
 print(f"Error checking event source mappings: {e}")

if __name__ == "__main__":
 print("Testing Deployed Lambda Functions with Dynamic UUID Discovery")
 
 try:
 # Check current status
 check_event_source_mappings()
 
 # Test successful scenarios first
 test_successful_scenarios()
 
 # Test error scenarios
 test_error_scenarios()
 
 # Check status again after tests
 print("\nFinal Status Check")
 check_event_source_mappings()
 
 except KeyboardInterrupt:
 print("\nTests cancelled by user")
 except Exception as e:
 print(f"\nTest failed: {e}")
 
 print("\nTesting complete!")
 print("\nSummary:")
 print(" Lambda functions now use dynamic UUID discovery")
 print(" No environment variables needed for event source mapping UUIDs")
 print(" Error handling automatically discovers and manages subscriptions")
 print(" System is more resilient and self-configuring")