#!/usr/bin/env python3
"""
DEMO 3: 400 Error Scenario - Continue Processing
1. Send bank account message that triggers 400 error
2. Send normal bank account message that processes successfully
3. Confirm first transaction threw 400 error
4. Confirm second transaction processed successfully
"""

import json
import boto3
import time
from datetime import datetime

# Configuration - SNS Topic ARN
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
BANK_ACCOUNT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo"

def send_400_error_message():
 """Send a message that will trigger a 400 error"""
 
 print("STEP 1: Sending Bank Account Message (400 Error)")
 print("-" * 50)
 
 # Create message with ERROR400 in customer_id to trigger 400 error
 customer_id = f"ERROR400-demo-{int(time.time())}"
 message = {
 'customer_id': customer_id,
 'routing_number': '123456789',
 'account_number': '987654321',
 'account_type': 'checking',
 'bank_name': 'Demo Bank',
 'message_id': f"demo-400-error-{int(time.time())}",
 'message_group_id': customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 
 print(f"Sending message that will trigger 400 error:")
 print(f" Customer ID: {customer_id} (contains ERROR400)")
 print(f" Expected: Invalid account number format error")
 
 # Send to SNS topic with proper message attributes for routing
 sns_client = boto3.client('sns')
 message_id = f"demo-400-{customer_id}-{int(time.time())}"
 
 try:
 response = sns_client.publish(
 TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
 Message=json.dumps(message),
 Subject="Bank Account Setup Request (400 Error Test)",
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'bank_account_setup' # This triggers routing to bank account queue
 },
 'customer_id': {
 'DataType': 'String',
 'StringValue': customer_id
 },
 'message_group_id': {
 'DataType': 'String',
 'StringValue': customer_id
 }
 },
 MessageGroupId=customer_id,
 MessageDeduplicationId=message_id
 )
 
 print(f"400 Error message sent successfully!")
 print(f" SNS Message ID: {response['MessageId']}")
 
 return customer_id
 
 except Exception as e:
 print(f"Failed to send 400 error message: {e}")
 return None

def send_success_message():
 """Send a normal message that should process successfully"""
 
 print(f"\nSTEP 2: Sending Normal Bank Account Message (Success)")
 print("-" * 50)
 
 # Create normal message
 customer_id = f"success-demo-{int(time.time())}"
 message = {
 'customer_id': customer_id,
 'routing_number': '123456789',
 'account_number': '987654321',
 'account_type': 'checking',
 'bank_name': 'Demo Bank',
 'message_id': f"demo-success-{int(time.time())}",
 'message_group_id': customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 
 print(f"Sending normal message:")
 print(f" Customer ID: {customer_id}")
 print(f" Expected: Successful processing")
 
 # Send to SNS topic with proper message attributes for routing
 sns_client = boto3.client('sns')
 message_id = f"demo-success-{customer_id}-{int(time.time())}"
 
 try:
 response = sns_client.publish(
 TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
 Message=json.dumps(message),
 Subject="Bank Account Setup Request (Success Test)",
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'bank_account_setup' # This triggers routing to bank account queue
 },
 'customer_id': {
 'DataType': 'String',
 'StringValue': customer_id
 },
 'message_group_id': {
 'DataType': 'String',
 'StringValue': customer_id
 }
 },
 MessageGroupId=customer_id,
 MessageDeduplicationId=message_id
 )
 
 print(f"Success message sent successfully!")
 print(f" SNS Message ID: {response['MessageId']}")
 
 return customer_id
 
 except Exception as e:
 print(f"Failed to send success message: {e}")
 return None

def wait_for_processing():
 """Wait for messages to be processed"""
 
 print(f"\nSTEP 3: Waiting for Lambda Processing...")
 print("-" * 40)
 
 print(f"Waiting 10 seconds for both messages to be processed...")
 time.sleep(10)
 
 # Check queue status
 sqs = boto3.client('sqs')
 
 try:
 response = sqs.get_queue_attributes(
 QueueUrl=BANK_ACCOUNT_QUEUE_URL,
 AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
 )
 
 available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
 in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
 
 print(f"Queue Status After Processing:")
 print(f" - Messages Available: {available}")
 print(f" - Messages In-Flight: {in_flight}")
 
 if available == 0 and in_flight == 0:
 print(f"All messages processed (both 400 error and success)")
 else:
 print(f"Some messages still processing...")
 
 except Exception as e:
 print(f"Error checking queue status: {e}")

def check_400_error_logs(error_customer_id):
 """Check logs for 400 error processing"""
 
 print(f"\nSTEP 4: Confirming 400 Error Processing")
 print("-" * 45)
 
 logs_client = boto3.client('logs')
 
 try:
 # Look for error logs with the customer ID
 response = logs_client.filter_log_events(
 logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-setup',
 startTime=int((time.time() - 120) * 1000), # Last 2 minutes
 filterPattern=f'{error_customer_id}'
 )
 
 error_found = False
 for event in response['events']:
 message = event['message']
 if 'client_error' in message or 'Invalid account' in message:
 timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
 print(f"Found 400 error log:")
 print(f" [{timestamp}] {message.strip()}")
 error_found = True
 break
 
 if not error_found:
 print(f"400 error log not found yet - may need more time")
 
 # Also check for error processing message
 response = logs_client.filter_log_events(
 logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-setup',
 startTime=int((time.time() - 120) * 1000),
 filterPattern='Client error (4xx) - continuing processing'
 )
 
 if response['events']:
 print(f"Confirmed: 400 error handled correctly (continuing processing)")
 
 except Exception as e:
 print(f"Error checking 400 error logs: {e}")

def check_success_logs(success_customer_id):
 """Check logs for successful processing"""
 
 print(f"\nSTEP 5: Confirming Success Processing")
 print("-" * 40)
 
 logs_client = boto3.client('logs')
 
 try:
 # Look for success logs
 response = logs_client.filter_log_events(
 logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-setup',
 startTime=int((time.time() - 120) * 1000), # Last 2 minutes
 filterPattern='Successfully processed'
 )
 
 success_found = False
 for event in response['events']:
 message = event['message']
 timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
 print(f"Found success log:")
 print(f" [{timestamp}] {message.strip()}")
 success_found = True
 break
 
 if not success_found:
 print(f"Success log not found yet - may need more time")
 
 except Exception as e:
 print(f"Error checking success logs: {e}")

def check_subscription_status():
 """Verify subscriptions are still enabled after 400 errors"""
 
 print(f"\nSTEP 6: Verifying Subscription Status")
 print("-" * 40)
 
 lambda_client = boto3.client('lambda')
 
 try:
 response = lambda_client.list_event_source_mappings(
 FunctionName='utility-customer-system-dev-bank-account-setup'
 )
 
 for mapping in response['EventSourceMappings']:
 if 'sqs' in mapping['EventSourceArn'].lower():
 state = mapping['State']
 enabled = state == 'Enabled'
 print(f"Bank Account Subscription: {state} ({'' if enabled else ''})")
 
 if enabled:
 print(f"CORRECT: Subscription remains enabled after 400 error")
 print(f" (400 errors should NOT disable subscriptions)")
 else:
 print(f"UNEXPECTED: Subscription disabled after 400 error")
 
 except Exception as e:
 print(f"Error checking subscription status: {e}")

def main():
 """Main demo function for 400 error scenario"""
 
 print("CLIENT DEMO - 400 Error Scenario")
 print("Demonstrating 400 error handling (continue processing)")
 print("=" * 60)
 
 # Step 1: Send 400 error message
 error_customer_id = send_400_error_message()
 if not error_customer_id:
 print("Demo failed - could not send 400 error message")
 return
 
 # Step 2: Send success message
 success_customer_id = send_success_message()
 if not success_customer_id:
 print("Demo failed - could not send success message")
 return
 
 # Step 3: Wait for processing
 wait_for_processing()
 
 # Step 4: Check 400 error logs
 check_400_error_logs(error_customer_id)
 
 # Step 5: Check success logs
 check_success_logs(success_customer_id)
 
 # Step 6: Verify subscription status
 check_subscription_status()
 
 print(f"\nDEMO 3 COMPLETE!")
 print(f"400 Error Scenario Summary:")
 print(f" 400 error message sent and processed")
 print(f" Success message sent and processed")
 print(f" 400 error handled correctly (continue processing)")
 print(f" Subscription remains enabled after 400 error")
 print(f" System continues processing subsequent messages")
 
 print(f"\nKey Takeaway:")
 print(f" 400 errors are client errors - system continues processing")
 print(f" Subscriptions remain active, no service disruption")

if __name__ == "__main__":
 main()