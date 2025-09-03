#!/usr/bin/env python3
"""
Debug script to check current queue and subscription status
"""

import boto3
import json

# Configuration
BANK_ACCOUNT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo"
PAYMENT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"

def check_current_status():
 """Check current queue and subscription status"""
 
 print("DEBUGGING: Current System Status")
 print("=" * 40)
 
 # Check queue status
 print("\nQueue Status:")
 print("-" * 20)
 
 sqs = boto3.client('sqs')
 
 queues = [
 ('Bank Account', BANK_ACCOUNT_QUEUE_URL),
 ('Payment', PAYMENT_QUEUE_URL)
 ]
 
 total_messages = 0
 
 for queue_name, queue_url in queues:
 try:
 response = sqs.get_queue_attributes(
 QueueUrl=queue_url,
 AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
 )
 
 available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
 in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
 total = available + in_flight
 total_messages += total
 
 print(f" {queue_name}: {available} available, {in_flight} in-flight, {total} total")
 
 except Exception as e:
 print(f" Error checking {queue_name}: {e}")
 
 print(f"\n Total Messages Across All Queues: {total_messages}")
 
 # Check subscription status
 print("\nSubscription Status:")
 print("-" * 25)
 
 lambda_client = boto3.client('lambda')
 
 functions = [
 ('Bank Account', 'utility-customer-system-dev-bank-account-setup'),
 ('Payment', 'utility-customer-system-dev-payment-processing')
 ]
 
 for service_name, function_name in functions:
 try:
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 for mapping in response['EventSourceMappings']:
 if 'sqs' in mapping['EventSourceArn'].lower():
 state = mapping['State']
 uuid = mapping['UUID']
 print(f" {service_name}: {state} (UUID: {uuid})")
 
 except Exception as e:
 print(f" Error checking {service_name}: {e}")
 
 # Provide recommendations
 print(f"\nAnalysis:")
 print("-" * 15)
 
 if total_messages > 0:
 print(f"{total_messages} messages still in queues")
 print(f" Possible causes:")
 print(f" 1. Subscriptions may still be disabled")
 print(f" 2. Subscriptions may be enabling (in progress)")
 print(f" 3. Messages may be processing slowly")
 print(f" 4. Lambda functions may need more time")
 
 print(f"\nRecommended actions:")
 print(f" 1. Check if subscriptions are enabled above")
 print(f" 2. If disabled, run: python3 demo_enable_subscriptions.py")
 print(f" 3. Wait a few more minutes for processing")
 print(f" 4. Check CloudWatch logs for errors")
 
 else:
 print(f"All queues are empty - system is working correctly!")

if __name__ == "__main__":
 check_current_status()