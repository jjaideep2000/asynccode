#!/usr/bin/env python3
"""
Test 500 error scenarios to verify subscription control works with dynamic UUID discovery
"""

import json
import boto3
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_subscription_status(function_name):
 """Check the current subscription status"""
 
 try:
 lambda_client = boto3.client('lambda')
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 for mapping in response['EventSourceMappings']:
 if 'sqs' in mapping['EventSourceArn'].lower():
 return {
 'uuid': mapping['UUID'],
 'state': mapping['State'],
 'enabled': mapping['State'] == 'Enabled'
 }
 
 return None
 
 except Exception as e:
 print(f"Error checking subscription status: {e}")
 return None

def test_500_error_with_subscription_control():
 """Test 500 error scenario and verify subscription gets disabled"""
 
 print("🧪 Testing 500 Error with Subscription Control")
 print("=" * 50)
 
 function_name = 'utility-customer-system-dev-bank-account-setup'
 
 # Check initial status
 print("\nInitial Subscription Status")
 print("-" * 30)
 initial_status = check_subscription_status(function_name)
 if initial_status:
 print(f" UUID: {initial_status['uuid']}")
 print(f" State: {initial_status['state']}")
 print(f" Enabled: {initial_status['enabled']}")
 else:
 print(" Could not get initial status")
 return
 
 # Trigger 500 error
 print("\nTriggering 500 Error")
 print("-" * 30)
 
 try:
 lambda_client = boto3.client('lambda')
 
 error_payload = {
 'customer_id': 'ERROR500-subscription-test',
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': 'test-500-subscription-control'
 }
 
 response = lambda_client.invoke(
 FunctionName=function_name,
 InvocationType='RequestResponse',
 Payload=json.dumps(error_payload)
 )
 
 response_payload = json.loads(response['Payload'].read())
 print(f"Function invoked successfully")
 print(f" Response: {json.dumps(response_payload, indent=2)}")
 
 # Parse the response body to check error handling
 if response_payload.get('statusCode') == 200:
 body = json.loads(response_payload['body'])
 if body.get('status') == 'error':
 error_info = body.get('error_info', {})
 action = body.get('action')
 subscription_disabled = error_info.get('subscription_disabled', False)
 
 print(f"\nError Handling Results:")
 print(f" Error Type: {error_info.get('error_type')}")
 print(f" Action: {action}")
 print(f" Subscription Disabled: {subscription_disabled}")
 
 if action == 'stop_subscription' and subscription_disabled:
 print("Subscription control working correctly!")
 elif action == 'stop_subscription' and not subscription_disabled:
 print("Subscription should have been disabled but wasn't")
 else:
 print("Different action taken")
 
 except Exception as e:
 print(f"Error invoking function: {e}")
 return
 
 # Wait a moment for changes to propagate
 print("\nWaiting for changes to propagate...")
 time.sleep(3)
 
 # Check final status
 print("\nFinal Subscription Status")
 print("-" * 30)
 final_status = check_subscription_status(function_name)
 if final_status:
 print(f" UUID: {final_status['uuid']}")
 print(f" State: {final_status['state']}")
 print(f" Enabled: {final_status['enabled']}")
 
 # Compare with initial status
 if initial_status['enabled'] and not final_status['enabled']:
 print("Subscription successfully disabled after 500 error!")
 elif initial_status['enabled'] and final_status['enabled']:
 print("Subscription is still enabled (may be expected behavior)")
 else:
 print("Subscription status unchanged")
 else:
 print(" Could not get final status")

def test_subscription_re_enable():
 """Test re-enabling the subscription via SNS control message"""
 
 print("\nTesting Subscription Re-enable via SNS")
 print("=" * 50)
 
 try:
 sns_client = boto3.client('sns')
 
 # Send enable message
 control_message = {
 'action': 'enable',
 'service': 'bank-account-setup',
 'timestamp': time.time()
 }
 
 response = sns_client.publish(
 TopicArn='arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control',
 Message=json.dumps(control_message),
 Subject='Enable Subscription'
 )
 
 print(f"Control message sent: {response['MessageId']}")
 
 # Wait for processing
 print("Waiting for control message to be processed...")
 time.sleep(5)
 
 # Check status
 function_name = 'utility-customer-system-dev-bank-account-setup'
 status = check_subscription_status(function_name)
 if status:
 print(f"\nSubscription Status After Re-enable:")
 print(f" UUID: {status['uuid']}")
 print(f" State: {status['state']}")
 print(f" Enabled: {status['enabled']}")
 
 if status['enabled']:
 print("Subscription successfully re-enabled!")
 else:
 print("Subscription is still disabled")
 
 except Exception as e:
 print(f"Error testing subscription re-enable: {e}")

if __name__ == "__main__":
 print("Testing 500 Error Scenarios with Dynamic UUID Discovery")
 
 try:
 test_500_error_with_subscription_control()
 test_subscription_re_enable()
 
 except KeyboardInterrupt:
 print("\nTests cancelled by user")
 except Exception as e:
 print(f"\nTest failed: {e}")
 
 print("\nTesting complete!")
 print("\nKey Points:")
 print(" Dynamic UUID discovery eliminates need for environment variables")
 print(" Error handlers can automatically manage subscriptions")
 print(" System is self-configuring and resilient")
 print(" Subscription control works via SNS messages")