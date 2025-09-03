#!/usr/bin/env python3
"""
Test error handling scenarios
"""

import json
import boto3
import random
import time
from datetime import datetime

# Load outputs
with open('../deploy/outputs_simple.json', 'r') as f:
 outputs = json.load(f)

# Initialize AWS clients
sns_client = boto3.client('sns', region_name=outputs['region'])
sqs_client = boto3.client('sqs', region_name=outputs['region'])

print("ERROR HANDLING TEST")
print("=" * 40)

def send_transaction_message(transaction_type, customer_id, **kwargs):
 """Send transaction message to FIFO SNS topic"""
 
 message_id = f"{transaction_type}-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"
 
 message = {
 "message_id": message_id,
 "transaction_type": transaction_type,
 "customer_id": customer_id,
 "message_group_id": customer_id, # Required for FIFO ordering
 "timestamp": datetime.now().isoformat(),
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

def send_subscription_control(action):
 """Send subscription control message"""
 
 control_message = {
 "action": action,
 "timestamp": datetime.now().isoformat(),
 "reason": f"Test {action} command"
 }
 
 response = sns_client.publish(
 TopicArn=outputs['subscription_control_topic_arn'],
 Message=json.dumps(control_message),
 Subject=f"Subscription Control: {action.upper()}"
 )
 
 print(f"Sent subscription control: {action}")
 return response['MessageId']

# Test 1: 400 Errors (should continue processing)
print("\nTesting 400 Errors (should continue processing)")
print("-" * 50)

send_transaction_message(
 "bank_account_setup", 
 "CUST-ERROR400-BANK",
 routing_number="123456789",
 account_number="9876543210",
 account_type="checking"
)

send_transaction_message(
 "payment",
 "CUST-ERROR400-PAY",
 amount=150.00,
 payment_method="bank_account",
 bill_type="utility"
)

print("400 error messages sent - Lambdas should continue processing")

# Test 2: 500 Errors (should stop subscription)
print("\nTesting 500 Errors (should stop subscription)")
print("-" * 50)

send_transaction_message(
 "bank_account_setup", 
 "CUST-ERROR500-BANK",
 routing_number="123456789",
 account_number="9876543210",
 account_type="checking"
)

send_transaction_message(
 "payment",
 "CUST-ERROR500-PAY",
 amount=200.00,
 payment_method="bank_account",
 bill_type="utility"
)

print("500 error messages sent - Lambdas should stop processing")

# Wait for processing
print("\nWaiting for error processing...")
time.sleep(10)

# Test 3: Send messages while subscription might be stopped
print("\n📦 Sending messages (should pile up if subscription stopped)")
print("-" * 50)

for i in range(3):
 send_transaction_message(
 "bank_account_setup", 
 f"CUST-PILEUP-{i:03d}",
 routing_number="123456789",
 account_number="9876543210",
 account_type="checking"
 )
 
 send_transaction_message(
 "payment",
 f"CUST-PILEUP-{i:03d}",
 amount=100.00 + i * 10,
 payment_method="bank_account",
 bill_type="utility"
 )

print("Pileup messages sent")

# Test 4: Restart subscriptions
print("\n🔄 Restarting subscriptions")
print("-" * 30)

send_subscription_control("start")

print("\nWaiting for restart processing...")
time.sleep(15)

# Final status check
def check_queue_depth(queue_url):
 """Check number of messages in queue"""
 response = sqs_client.get_queue_attributes(
 QueueUrl=queue_url,
 AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
 )
 
 visible = int(response['Attributes']['ApproximateNumberOfMessages'])
 not_visible = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
 
 return visible, not_visible

print("\nFinal Queue Status:")
print("-" * 25)

bank_visible, bank_not_visible = check_queue_depth(outputs['bank_account_setup_queue_url'])
payment_visible, payment_not_visible = check_queue_depth(outputs['payment_processing_queue_url'])

print(f"Bank Account Queue: {bank_visible} visible, {bank_not_visible} processing")
print(f"Payment Queue: {payment_visible} visible, {payment_not_visible} processing")

print("\nERROR HANDLING TEST COMPLETED!")
print("\nWhat was tested:")
print("400 errors - Lambdas continue processing")
print("500 errors - Lambdas stop processing") 
print("Message pileup during stopped state")
print("Subscription restart functionality")
print("\nCheck CloudWatch logs for detailed error handling behavior!")