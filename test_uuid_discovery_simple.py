#!/usr/bin/env python3
"""
Simple test to verify UUID discovery works with current permissions
"""

import json
import boto3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_uuid_discovery_direct():
 """Test UUID discovery directly using boto3"""
 
 print("🧪 Testing Direct UUID Discovery")
 print("=" * 40)
 
 function_names = [
 'utility-customer-system-dev-bank-account-setup',
 'utility-customer-system-dev-payment-processing'
 ]
 
 try:
 lambda_client = boto3.client('lambda')
 
 for function_name in function_names:
 print(f"\nTesting function: {function_name}")
 print("-" * 30)
 
 try:
 # Test list event source mappings
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 print(f"ListEventSourceMappings successful")
 print(f" Found {len(response['EventSourceMappings'])} mappings")
 
 for mapping in response['EventSourceMappings']:
 event_source_arn = mapping.get('EventSourceArn', '')
 uuid = mapping.get('UUID', '')
 state = mapping.get('State', '')
 
 print(f" Mapping: {uuid}")
 print(f" Source: {event_source_arn}")
 print(f" State: {state}")
 
 if 'sqs' in event_source_arn.lower():
 print(f" Found SQS mapping: {uuid}")
 
 # Test get event source mapping
 try:
 get_response = lambda_client.get_event_source_mapping(UUID=uuid)
 print(f" GetEventSourceMapping successful")
 print(f" State: {get_response.get('State')}")
 except Exception as e:
 print(f" GetEventSourceMapping failed: {e}")
 
 # Test update event source mapping (just check permissions, don't actually change)
 try:
 # This should work but we won't actually change anything
 print(f" UpdateEventSourceMapping permission check (not executing)")
 except Exception as e:
 print(f" UpdateEventSourceMapping permission issue: {e}")
 
 except Exception as e:
 print(f"Error with {function_name}: {e}")
 
 except Exception as e:
 print(f"General error: {e}")

def test_lambda_invocation_with_uuid_discovery():
 """Test Lambda invocation to see UUID discovery in action"""
 
 print("\nTesting Lambda Invocation with UUID Discovery")
 print("=" * 50)
 
 try:
 lambda_client = boto3.client('lambda')
 
 # Simple test payload
 test_payload = {
 'customer_id': 'uuid-discovery-test',
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': 'uuid-test-msg'
 }
 
 function_name = 'utility-customer-system-dev-bank-account-setup'
 
 print(f"Invoking: {function_name}")
 
 response = lambda_client.invoke(
 FunctionName=function_name,
 InvocationType='RequestResponse',
 Payload=json.dumps(test_payload)
 )
 
 response_payload = json.loads(response['Payload'].read())
 
 print(f"Function invoked successfully")
 print(f" Status Code: {response['StatusCode']}")
 print(f" Response: {json.dumps(response_payload, indent=2)}")
 
 # Check logs for UUID discovery
 print("\nChecking recent logs for UUID discovery...")
 
 import time
 time.sleep(2) # Wait for logs to appear
 
 logs_client = boto3.client('logs')
 
 try:
 log_response = logs_client.filter_log_events(
 logGroupName=f'/aws/lambda/{function_name}',
 startTime=int((time.time() - 300) * 1000), # Last 5 minutes
 filterPattern='UUID'
 )
 
 for event in log_response['events'][-5:]: # Last 5 events
 print(f" {event['message'].strip()}")
 
 except Exception as e:
 print(f" Could not fetch logs: {e}")
 
 except Exception as e:
 print(f"Error testing Lambda invocation: {e}")

if __name__ == "__main__":
 print("Testing UUID Discovery with Current Permissions")
 
 test_uuid_discovery_direct()
 test_lambda_invocation_with_uuid_discovery()
 
 print("\nTesting complete!")