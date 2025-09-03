#!/usr/bin/env python3
"""
Check system status
"""

import json
import boto3
import time

# Load outputs
with open('../deploy/outputs_simple.json', 'r') as f:
 outputs = json.load(f)

# Initialize AWS clients
sqs_client = boto3.client('sqs', region_name=outputs['region'])
lambda_client = boto3.client('lambda', region_name=outputs['region'])

def check_queue_depth(queue_url):
 """Check number of messages in queue"""
 response = sqs_client.get_queue_attributes(
 QueueUrl=queue_url,
 AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
 )
 
 visible = int(response['Attributes']['ApproximateNumberOfMessages'])
 not_visible = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
 
 return visible, not_visible

def check_lambda_status(function_name):
 """Check Lambda function status"""
 try:
 response = lambda_client.get_function(FunctionName=function_name)
 return response['Configuration']['State']
 except Exception as e:
 return f"Error: {e}"

print("SYSTEM STATUS CHECK")
print("=" * 40)

# Check Lambda functions
print("\nLambda Function Status:")
bank_status = check_lambda_status(outputs['bank_account_lambda_name'])
payment_status = check_lambda_status(outputs['payment_lambda_name'])

print(f"Bank Account Lambda: {bank_status}")
print(f"Payment Lambda: {payment_status}")

# Check queue depths multiple times
print("\nQueue Status (checking multiple times):")

for i in range(3):
 print(f"\nCheck #{i+1}:")
 
 bank_visible, bank_not_visible = check_queue_depth(outputs['bank_account_setup_queue_url'])
 payment_visible, payment_not_visible = check_queue_depth(outputs['payment_processing_queue_url'])
 
 print(f"Bank Account Queue: {bank_visible} visible, {bank_not_visible} processing")
 print(f"Payment Queue: {payment_visible} visible, {payment_not_visible} processing")
 
 if i < 2: # Don't sleep after last check
 time.sleep(5)

print("\nStatus check completed!")