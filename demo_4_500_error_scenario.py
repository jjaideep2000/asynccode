#!/usr/bin/env python3
"""
DEMO 4: 500 Error Scenario - Subscription Control
1. Send bank account message that triggers 500 error
2. Send payment message that triggers 500 error 
3. Send more normal messages (should pile up)
4. Confirm messages are piled up in queues
5. Send resubscribe message on SNS topic
6. Confirm Lambda functions resubscribe and process messages
7. Confirm queues are emptied
"""

import json
import boto3
import time
from datetime import datetime

# Configuration - SNS Topic ARN and Queue URLs for monitoring
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
BANK_ACCOUNT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo"
PAYMENT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"
SUBSCRIPTION_CONTROL_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"

def send_500_error_messages():
 """Send messages that will trigger 500 errors"""
 
 print("STEP 1: Sending Messages to Trigger 500 Errors")
 print("-" * 50)
 
 sns_client = boto3.client('sns')
 
 # Send bank account 500 error
 bank_customer_id = f"ERROR500-bank-demo-{int(time.time())}"
 bank_message = {
 'customer_id': bank_customer_id,
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': f"demo-500-bank-{int(time.time())}",
 'message_group_id': bank_customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 
 print(f"Sending Bank Account 500 Error Message:")
 print(f" Customer ID: {bank_customer_id} (contains ERROR500)")
 print(f" Expected: Bank validation service unavailable")
 
 try:
 response = sns_client.publish(
 TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
 Message=json.dumps(bank_message),
 Subject="Bank Account Setup Request (500 Error Test)",
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'bank_account_setup'
 },
 'customer_id': {
 'DataType': 'String',
 'StringValue': bank_customer_id
 },
 'message_group_id': {
 'DataType': 'String',
 'StringValue': bank_customer_id
 }
 },
 MessageGroupId=bank_customer_id,
 MessageDeduplicationId=f"demo-500-bank-{bank_customer_id}-{int(time.time())}"
 )
 print(f" Bank Account 500 error message sent: {response['MessageId']}")
 except Exception as e:
 print(f" Failed to send bank account 500 error: {e}")
 return None, None
 
 # Send payment 500 error
 payment_customer_id = f"ERROR500-payment-demo-{int(time.time())}"
 payment_message = {
 'customer_id': payment_customer_id,
 'amount': 150.00,
 'payment_method': 'bank_account',
 'message_id': f"demo-500-payment-{int(time.time())}",
 'message_group_id': payment_customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 
 print(f"\nSending Payment 500 Error Message:")
 print(f" Customer ID: {payment_customer_id} (contains ERROR500)")
 print(f" Expected: Payment gateway unavailable")
 
 try:
 response = sns_client.publish(
 TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
 Message=json.dumps(payment_message),
 Subject="Payment Processing Request (500 Error Test)",
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'payment'
 },
 'customer_id': {
 'DataType': 'String',
 'StringValue': payment_customer_id
 },
 'message_group_id': {
 'DataType': 'String',
 'StringValue': payment_customer_id
 }
 },
 MessageGroupId=payment_customer_id,
 MessageDeduplicationId=f"demo-500-payment-{payment_customer_id}-{int(time.time())}"
 )
 print(f" Payment 500 error message sent: {response['MessageId']}")
 except Exception as e:
 print(f" Failed to send payment 500 error: {e}")
 return bank_customer_id, None
 
 return bank_customer_id, payment_customer_id

def wait_for_500_errors():
 """Wait for 500 errors to be processed and subscriptions disabled"""
 
 print(f"\nSTEP 2: Waiting for 500 Error Processing & Subscription Disable")
 print("-" * 60)
 
 print(f"Waiting 15 seconds for 500 errors to disable subscriptions...")
 time.sleep(15)
 
 # Check subscription status
 lambda_client = boto3.client('lambda')
 
 functions = [
 ('Bank Account', 'utility-customer-system-dev-bank-account-setup'),
 ('Payment', 'utility-customer-system-dev-payment-processing')
 ]
 
 print(f"\nSubscription Status After 500 Errors:")
 
 disabled_count = 0
 for service_name, function_name in functions:
 try:
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 for mapping in response['EventSourceMappings']:
 if 'sqs' in mapping['EventSourceArn'].lower():
 state = mapping['State']
 enabled = state == 'Enabled'
 print(f" {service_name}: {state} ({'' if enabled else ''})")
 
 if not enabled:
 disabled_count += 1
 
 except Exception as e:
 print(f" Error checking {service_name}: {e}")
 
 if disabled_count > 0:
 print(f"\nSUCCESS: {disabled_count} subscription(s) disabled by 500 errors")
 else:
 print(f"\nNo subscriptions disabled yet - may need more time")
 
 return disabled_count > 0

def send_normal_messages():
 """Send normal messages that should pile up"""
 
 print(f"\nSTEP 3: Sending Normal Messages (Should Pile Up)")
 print("-" * 50)
 
 sns_client = boto3.client('sns')
 
 print(f"Sending 3 bank account messages and 3 payment messages...")
 
 # Send bank account messages
 for i in range(3):
 customer_id = f"normal-bank-{i+1}-{int(time.time())}"
 message = {
 'customer_id': customer_id,
 'routing_number': '123456789',
 'account_number': f"10012345{i}",
 'message_id': f"normal-bank-{i+1}-{int(time.time())}",
 'message_group_id': customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 
 try:
 sns_client.publish(
 TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
 Message=json.dumps(message),
 Subject=f"Bank Account Setup Request {i+1}",
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'bank_account_setup'
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
 MessageDeduplicationId=f"normal-bank-{i}-{int(time.time())}"
 )
 print(f" Bank message {i+1} sent: {customer_id}")
 except Exception as e:
 print(f" Failed bank message {i+1}: {e}")
 
 # Send payment messages
 for i in range(3):
 customer_id = f"normal-payment-{i+1}-{int(time.time())}"
 message = {
 'customer_id': customer_id,
 'amount': 50.00 + (i * 25),
 'payment_method': 'bank_account',
 'message_id': f"normal-payment-{i+1}-{int(time.time())}",
 'message_group_id': customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 
 try:
 sns_client.publish(
 TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
 Message=json.dumps(message),
 Subject=f"Payment Processing Request {i+1}",
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'payment'
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
 MessageDeduplicationId=f"normal-payment-{i}-{int(time.time())}"
 )
 print(f" Payment message {i+1} sent: {customer_id}")
 except Exception as e:
 print(f" Failed payment message {i+1}: {e}")

def check_message_pileup():
 """Check that messages are piling up in queues"""
 
 print(f"\nSTEP 4: Confirming Messages Are Piling Up")
 print("-" * 45)
 
 print(f"Waiting 10 seconds for messages to pile up...")
 time.sleep(10)
 
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
 
 print(f"{queue_name} Queue:")
 print(f" - Available: {available}")
 print(f" - In-Flight: {in_flight}")
 print(f" - Total: {total}")
 
 except Exception as e:
 print(f"Error checking {queue_name} queue: {e}")
 
 if total_messages > 0:
 print(f"\nSUCCESS: {total_messages} messages piled up in queues")
 print(f" (Subscriptions disabled - messages not being processed)")
 else:
 print(f"\nNo messages piled up - subscriptions may still be active")
 
 return total_messages

def send_resubscribe_message():
 """Send resubscribe message on SNS topic"""
 
 print(f"\nSTEP 5: Sending Resubscribe Message on SNS Topic")
 print("-" * 50)
 
 sns = boto3.client('sns')
 
 control_message = {
 'action': 'enable',
 'timestamp': datetime.utcnow().isoformat(),
 'source': 'demo_500_scenario'
 }
 
 print(f"Sending resubscribe (enable) message:")
 print(f" Action: {control_message['action']}")
 print(f" Topic: Subscription Control")
 
 try:
 response = sns.publish(
 TopicArn=SUBSCRIPTION_CONTROL_TOPIC_ARN,
 Message=json.dumps(control_message),
 Subject='Demo: Resubscribe All Services'
 )
 
 print(f"Resubscribe message sent successfully!")
 print(f" SNS Message ID: {response['MessageId']}")
 
 return True
 
 except Exception as e:
 print(f"Failed to send resubscribe message: {e}")
 return False

def wait_for_resubscription():
 """Wait for Lambda functions to resubscribe"""
 
 print(f"\nSTEP 6: Waiting for Lambda Functions to Resubscribe")
 print("-" * 50)
 
 print(f"Waiting 15 seconds for resubscription...")
 time.sleep(15)
 
 # Check subscription status
 lambda_client = boto3.client('lambda')
 
 functions = [
 ('Bank Account', 'utility-customer-system-dev-bank-account-setup'),
 ('Payment', 'utility-customer-system-dev-payment-processing')
 ]
 
 print(f"\nSubscription Status After Resubscribe:")
 
 enabled_count = 0
 for service_name, function_name in functions:
 try:
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 for mapping in response['EventSourceMappings']:
 if 'sqs' in mapping['EventSourceArn'].lower():
 state = mapping['State']
 enabled = state == 'Enabled'
 print(f" {service_name}: {state} ({'' if enabled else ''})")
 
 if enabled:
 enabled_count += 1
 
 except Exception as e:
 print(f" Error checking {service_name}: {e}")
 
 if enabled_count > 0:
 print(f"\nSUCCESS: {enabled_count} subscription(s) re-enabled")
 else:
 print(f"\nNo subscriptions re-enabled yet - may need more time")
 
 return enabled_count > 0

def check_message_processing():
 """Check that messages are being processed and queues emptied"""
 
 print(f"\nSTEP 7: Confirming Message Processing & Queue Emptying")
 print("-" * 55)
 
 sqs = boto3.client('sqs')
 
 # Monitor for 30 seconds
 for check in range(6): # 6 checks, 5 seconds apart
 print(f"\nCheck {check + 1}/6 (after {check * 5} seconds):")
 
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
 
 print(f" {queue_name}: {available} available, {in_flight} in-flight")
 
 except Exception as e:
 print(f" Error checking {queue_name}: {e}")
 
 if total_messages == 0:
 print(f"\nSUCCESS: All queues empty - messages processed!")
 break
 elif check < 5: # Don't sleep on last iteration
 time.sleep(5)
 
 if total_messages > 0:
 print(f"\n{total_messages} messages still in queues - may need more time")
 
 return total_messages == 0

def main():
 """Main demo function for 500 error scenario"""
 
 print("CLIENT DEMO - 500 Error Scenario")
 print("Demonstrating 500 error handling (subscription control)")
 print("=" * 65)
 
 # Step 1: Send 500 error messages
 bank_error_id, payment_error_id = send_500_error_messages()
 if not bank_error_id or not payment_error_id:
 print("Demo failed - could not send 500 error messages")
 return
 
 # Step 2: Wait for 500 errors and subscription disable
 subscriptions_disabled = wait_for_500_errors()
 
 # Step 3: Send normal messages
 send_normal_messages()
 
 # Step 4: Check message pileup
 messages_piled = check_message_pileup()
 
 # Step 5: Send resubscribe message
 resubscribe_sent = send_resubscribe_message()
 if not resubscribe_sent:
 print("Demo failed - could not send resubscribe message")
 return
 
 # Step 6: Wait for resubscription
 resubscribed = wait_for_resubscription()
 
 # Step 7: Check message processing
 queues_emptied = check_message_processing()
 
 print(f"\nDEMO 4 COMPLETE!")
 print(f"500 Error Scenario Summary:")
 print(f" 500 error messages sent and processed")
 print(f" {'' if subscriptions_disabled else ''} Subscriptions disabled by 500 errors")
 print(f" {'' if messages_piled else ''} Messages piled up in queues")
 print(f" Resubscribe message sent via SNS")
 print(f" {'' if resubscribed else ''} Lambda functions resubscribed")
 print(f" {'' if queues_emptied else ''} Queues emptied after resubscription")
 
 print(f"\nKey Takeaway:")
 print(f" 500 errors disable subscriptions to prevent cascade failures")
 print(f" SNS control messages can re-enable processing")
 print(f" System provides resilience and recovery mechanisms")

if __name__ == "__main__":
 main()