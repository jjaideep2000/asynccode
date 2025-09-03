#!/usr/bin/env python3
"""
Test 500 error handling in detail to see why subscription control isn't working
"""

import json
import boto3
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_500_error_direct_invocation():
 """Test 500 error by directly invoking Lambda function"""
 
 print("🧪 Testing 500 Error with Direct Lambda Invocation")
 print("=" * 50)
 
 lambda_client = boto3.client('lambda')
 
 # Test payload that should trigger 500 error
 test_payload = {
 'customer_id': 'ERROR500-direct-test',
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': 'direct-500-test'
 }
 
 function_name = 'utility-customer-system-dev-bank-account-setup'
 
 print(f"Invoking: {function_name}")
 print(f"Payload: {json.dumps(test_payload, indent=2)}")
 
 try:
 response = lambda_client.invoke(
 FunctionName=function_name,
 InvocationType='RequestResponse',
 Payload=json.dumps(test_payload)
 )
 
 response_payload = json.loads(response['Payload'].read())
 
 print(f"\nFunction Response:")
 print(f" Status Code: {response['StatusCode']}")
 print(f" Response: {json.dumps(response_payload, indent=2)}")
 
 # Parse the response body to check error handling details
 if response_payload.get('statusCode') == 200:
 body = json.loads(response_payload['body'])
 
 if body.get('status') == 'error':
 error_info = body.get('error_info', {})
 action = body.get('action')
 
 print(f"\nError Handling Analysis:")
 print(f" Error Type: {error_info.get('error_type')}")
 print(f" Error Message: {error_info.get('error_message')}")
 print(f" Status Code: {error_info.get('status_code')}")
 print(f" Action: {action}")
 print(f" Subscription Disabled: {error_info.get('subscription_disabled', 'Not reported')}")
 
 if action == 'stop_subscription':
 if 'subscription_disabled' in error_info:
 if error_info['subscription_disabled']:
 print(" Subscription successfully disabled")
 else:
 print(" Subscription disable failed")
 else:
 print(" Subscription disable status not reported")
 else:
 print(f" Action is '{action}', not 'stop_subscription'")
 
 return response_payload
 
 except Exception as e:
 print(f"Error invoking function: {e}")
 return None

def check_lambda_logs_detailed():
 """Check Lambda logs for detailed error information"""
 
 print("\nChecking Lambda Logs for Error Details")
 print("-" * 40)
 
 logs_client = boto3.client('logs')
 
 try:
 # Get recent log events
 response = logs_client.filter_log_events(
 logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-setup',
 startTime=int((time.time() - 300) * 1000), # Last 5 minutes
 filterPattern='ERROR500'
 )
 
 print(f"Found {len(response['events'])} log events with ERROR500:")
 
 for event in response['events'][-10:]: # Last 10 events
 timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
 message = event['message'].strip()
 print(f" [{timestamp}] {message}")
 
 # Also check for UUID discovery logs
 print(f"\nChecking for UUID Discovery Logs:")
 
 uuid_response = logs_client.filter_log_events(
 logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-setup',
 startTime=int((time.time() - 300) * 1000),
 filterPattern='UUID'
 )
 
 if uuid_response['events']:
 print(f"Found {len(uuid_response['events'])} UUID-related log events:")
 for event in uuid_response['events'][-5:]:
 timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
 message = event['message'].strip()
 print(f" [{timestamp}] {message}")
 else:
 print(" No UUID discovery logs found")
 
 # Check for subscription control logs
 print(f"\nChecking for Subscription Control Logs:")
 
 subscription_response = logs_client.filter_log_events(
 logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-setup',
 startTime=int((time.time() - 300) * 1000),
 filterPattern='subscription'
 )
 
 if subscription_response['events']:
 print(f"Found {len(subscription_response['events'])} subscription-related log events:")
 for event in subscription_response['events'][-5:]:
 timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
 message = event['message'].strip()
 print(f" [{timestamp}] {message}")
 else:
 print(" No subscription control logs found")
 
 except Exception as e:
 print(f"Error checking logs: {e}")

def test_uuid_discovery_in_lambda():
 """Test if UUID discovery is working by invoking a simple test"""
 
 print("\nTesting UUID Discovery in Lambda Environment")
 print("-" * 50)
 
 lambda_client = boto3.client('lambda')
 
 # Simple test payload that should succeed
 test_payload = {
 'customer_id': 'uuid-discovery-test',
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': 'uuid-discovery-test'
 }
 
 function_name = 'utility-customer-system-dev-bank-account-setup'
 
 print(f"Testing UUID discovery with successful message...")
 
 try:
 response = lambda_client.invoke(
 FunctionName=function_name,
 InvocationType='RequestResponse',
 Payload=json.dumps(test_payload)
 )
 
 response_payload = json.loads(response['Payload'].read())
 
 print(f"Function executed successfully")
 
 # Wait a moment then check logs for UUID discovery
 time.sleep(3)
 
 logs_client = boto3.client('logs')
 
 # Check for UUID discovery in recent logs
 uuid_response = logs_client.filter_log_events(
 logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-setup',
 startTime=int((time.time() - 60) * 1000), # Last minute
 filterPattern='Discovering'
 )
 
 if uuid_response['events']:
 print(f"UUID discovery logs found:")
 for event in uuid_response['events'][-3:]:
 message = event['message'].strip()
 print(f" {message}")
 else:
 print("No UUID discovery logs found - this indicates the issue")
 
 except Exception as e:
 print(f"Error testing UUID discovery: {e}")

def main():
 """Main test function"""
 
 print("Detailed 500 Error and Subscription Control Analysis")
 print("Investigating why subscription control isn't working")
 print("=" * 60)
 
 try:
 # Test 1: Direct invocation with 500 error
 test_500_error_direct_invocation()
 
 # Test 2: Check logs for details
 check_lambda_logs_detailed()
 
 # Test 3: Test UUID discovery
 test_uuid_discovery_in_lambda()
 
 print("\nAnalysis Summary")
 print("=" * 30)
 print("Expected behavior for 500 errors:")
 print(" 1. Error should be classified as 'server_error'")
 print(" 2. Action should be 'stop_subscription'")
 print(" 3. ❓ UUID should be discovered dynamically")
 print(" 4. ❓ Subscription should be disabled")
 print(" 5. ❓ 'subscription_disabled' should be true in response")
 
 print("\nIf UUID discovery is failing:")
 print(" - Check IAM permissions for lambda:ListEventSourceMappings")
 print(" - Verify error handler initialization")
 print(" - Check if boto3 client creation is working in Lambda")
 
 except KeyboardInterrupt:
 print("\nAnalysis cancelled by user")
 except Exception as e:
 print(f"\nAnalysis failed: {e}")
 import traceback
 traceback.print_exc()

if __name__ == "__main__":
 main()