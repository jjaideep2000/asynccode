#!/usr/bin/env python3
"""
Simple test for the FIFO utility customer system
"""

import json
import boto3
import random
from datetime import datetime

# Load outputs
with open('../deploy/outputs_simple.json', 'r') as f:
 outputs = json.load(f)

print("🧪 FIFO UTILITY CUSTOMER SYSTEM - SIMPLE TEST")
print("=" * 60)

# Initialize AWS clients
sns_client = boto3.client('sns', region_name=outputs['region'])
sqs_client = boto3.client('sqs', region_name=outputs['region'])

print(f"Region: {outputs['region']}")
print(f"Environment: {outputs['environment']}")
print(f"Transaction Topic: {outputs['transaction_processing_topic_arn']}")

def send_transaction_message(transaction_type, customer_id, **kwargs):
 """Send transaction message to FIFO SNS topic"""
 
 message_id = f"{transaction_type}-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"
 
 message = {
 "message_id": message_id,
 "transaction_type": transaction_type,
 "customer_id": customer_id,
 "message_group_id": customer_id, # Required for FIFO ordering
 "timestamp": datetime.utcnow().isoformat(),
 **kwargs
 }
 
 message_attributes = {
 'transaction_type': {
 'DataType': 'String',
 'StringValue': transaction_type
 },
 'customer_id': {
 'DataType': 'String',
 'StringValue': customer_id
 },
 'message_group_id': {
 'DataType': 'String',
 'StringValue': customer_id
 }
 }
 
 response = sns_client.publish(
 TopicArn=outputs['transaction_processing_topic_arn'],
 Message=json.dumps(message),
 Subject=f"Transaction: {transaction_type}",
 MessageAttributes=message_attributes,
 MessageGroupId=customer_id,
 MessageDeduplicationId=message_id
 )
 
 print(f"Sent {transaction_type} message for {customer_id}")
 return response['MessageId']

def check_queue_depth(queue_url):
 """Check number of messages in queue"""
 
 response = sqs_client.get_queue_attributes(
 QueueUrl=queue_url,
 AttributeNames=['ApproximateNumberOfMessages']
 )
 
 return int(response['Attributes']['ApproximateNumberOfMessages'])

# Test 1: Send bank account setup messages
print("\nTESTING BANK ACCOUNT SETUP")
print("=" * 40)

customers = ["CUST-HAPPY-001", "CUST-HAPPY-002", "CUST-ERROR400-TEST"]

for customer in customers:
 send_transaction_message(
 "bank_account_setup", 
 customer,
 routing_number=f"{random.randint(100000000, 999999999)}",
 account_number=f"{random.randint(1000000000, 9999999999)}",
 account_type="checking"
 )

# Test 2: Send payment messages
print("\n💳 TESTING PAYMENT PROCESSING")
print("=" * 40)

for customer in customers:
 amount = random.uniform(100, 500)
 send_transaction_message(
 "payment",
 customer,
 amount=round(amount, 2),
 payment_method="bank_account",
 bill_type="utility"
 )

# Test 3: Check queue depths
print("\nCHECKING QUEUE STATUS")
print("=" * 40)

import time
time.sleep(5) # Wait for message delivery

bank_depth = check_queue_depth(outputs['bank_account_setup_queue_url'])
payment_depth = check_queue_depth(outputs['payment_processing_queue_url'])

print(f"Bank Account Queue: {bank_depth} messages")
print(f"Payment Queue: {payment_depth} messages")

# Test 4: Send subscription control message
print("\nTESTING SUBSCRIPTION CONTROL")
print("=" * 40)

control_message = {
 "action": "start",
 "timestamp": datetime.utcnow().isoformat(),
 "reason": "Test restart command"
}

response = sns_client.publish(
 TopicArn=outputs['subscription_control_topic_arn'],
 Message=json.dumps(control_message),
 Subject="Subscription Control: START"
)

print(f"Sent subscription control message")

print("\nSIMPLE TEST COMPLETED!")
print("\nNext steps:")
print("1. Check AWS Lambda logs in CloudWatch")
print("2. Monitor queue processing")
print("3. Run the comprehensive test: python3 test_fifo_system.py")
print("4. Check CloudWatch metrics for observability")