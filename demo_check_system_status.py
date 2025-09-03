#!/usr/bin/env python3
"""
DEMO: Check overall system status before running demos
"""

import boto3
import json

def check_system_status():
 """Check the overall system status"""
 
 print("SYSTEM STATUS CHECK")
 print("=" * 30)
 
 # Check Lambda functions
 print("\nLambda Functions:")
 lambda_client = boto3.client('lambda')
 
 functions = [
 'utility-customer-system-dev-bank-account-setup',
 'utility-customer-system-dev-payment-processing'
 ]
 
 for function_name in functions:
 try:
 response = lambda_client.get_function(FunctionName=function_name)
 state = response['Configuration']['State']
 last_modified = response['Configuration']['LastModified']
 
 service_name = 'Bank Account' if 'bank-account' in function_name else 'Payment'
 print(f" {service_name}: {state} ({'' if state == 'Active' else ''})")
 print(f" Last Modified: {last_modified}")
 
 except Exception as e:
 print(f" Error checking {function_name}: {e}")
 
 # Check SQS queues
 print("\nSQS Queues:")
 sqs = boto3.client('sqs')
 
 queues = [
 ('Bank Account', 'https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo'),
 ('Payment', 'https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo')
 ]
 
 for queue_name, queue_url in queues:
 try:
 response = sqs.get_queue_attributes(
 QueueUrl=queue_url,
 AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
 )
 
 available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
 in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
 
 print(f" {queue_name}: {available} available, {in_flight} in-flight")
 
 except Exception as e:
 print(f" Error checking {queue_name} queue: {e}")
 
 # Check event source mappings (subscriptions)
 print("\nEvent Source Mappings (Subscriptions):")
 
 for function_name in functions:
 try:
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 service_name = 'Bank Account' if 'bank-account' in function_name else 'Payment'
 
 for mapping in response['EventSourceMappings']:
 if 'sqs' in mapping['EventSourceArn'].lower():
 state = mapping['State']
 enabled = state == 'Enabled'
 print(f" {service_name}: {state} ({'' if enabled else ''})")
 print(f" UUID: {mapping['UUID']}")
 
 except Exception as e:
 print(f" Error checking {function_name} mappings: {e}")
 
 print(f"\nSystem status check complete!")

if __name__ == "__main__":
 check_system_status()