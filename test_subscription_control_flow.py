#!/usr/bin/env python3
"""
Test the complete subscription control flow:
1. Send 500 error messages to disable Lambda subscriptions
2. Verify messages pile up in queues (not processed)
3. Re-enable subscriptions via SNS
4. Verify messages get processed again
"""

import json
import boto3
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BANK_ACCOUNT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo"
PAYMENT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"
SUBSCRIPTION_CONTROL_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"

LAMBDA_FUNCTIONS = [
 'utility-customer-system-dev-bank-account-setup',
 'utility-customer-system-dev-payment-processing'
]

def check_subscription_status():
 """Check current subscription status for both Lambda functions"""
 
 print("\nChecking Subscription Status")
 print("=" * 40)
 
 lambda_client = boto3.client('lambda')
 status = {}
 
 for function_name in LAMBDA_FUNCTIONS:
 try:
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 for mapping in response['EventSourceMappings']:
 if 'sqs' in mapping['EventSourceArn'].lower():
 uuid = mapping['UUID']
 state = mapping['State']
 enabled = state == 'Enabled'
 
 service_name = 'bank-account' if 'bank-account' in function_name else 'payment'
 status[service_name] = {
 'function': function_name,
 'uuid': uuid,
 'state': state,
 'enabled': enabled
 }
 
 print(f" {service_name.title()}: {state} ({'' if enabled else ''})")
 
 except Exception as e:
 print(f" Error checking {function_name}: {e}")
 
 return status

def check_queue_status():
 """Check message counts in both queues"""
 
 print("\nChecking Queue Status")
 print("=" * 30)
 
 sqs = boto3.client('sqs')
 queue_status = {}
 
 queues = [
 ('Bank Account', BANK_ACCOUNT_QUEUE_URL),
 ('Payment', PAYMENT_QUEUE_URL)
 ]
 
 for queue_name, queue_url in queues:
 try:
 response = sqs.get_queue_attributes(
 QueueUrl=queue_url,
 AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
 )
 
 available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
 in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
 
 queue_status[queue_name.lower().replace(' ', '_')] = {
 'available': available,
 'in_flight': in_flight,
 'total': available + in_flight
 }
 
 print(f" {queue_name}: {available} available, {in_flight} in-flight")
 
 except Exception as e:
 print(f" Error checking {queue_name} queue: {e}")
 
 return queue_status

def send_500_error_message(service_type):
 """Send a message that will trigger a 500 error"""
 
 sqs = boto3.client('sqs')
 
 customer_id = f"ERROR500-{service_type}-{int(time.time())}"
 message_id = f"500-error-{service_type}-{int(time.time())}"
 
 if service_type == 'bank-account':
 message_body = {
 'customer_id': customer_id,
 'routing_number': '123456789',
 'account_number': '987654321',
 'message_id': message_id,
 'message_group_id': customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 queue_url = BANK_ACCOUNT_QUEUE_URL
 else: # payment
 message_body = {
 'customer_id': customer_id,
 'amount': 150.00,
 'payment_method': 'bank_account',
 'message_id': message_id,
 'message_group_id': customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 queue_url = PAYMENT_QUEUE_URL
 
 try:
 response = sqs.send_message(
 QueueUrl=queue_url,
 MessageBody=json.dumps(message_body),
 MessageGroupId=customer_id,
 MessageDeduplicationId=f"{message_id}-{int(time.time())}"
 )
 
 print(f"Sent 500 error message for {service_type}: {customer_id}")
 return True
 
 except Exception as e:
 print(f"Failed to send 500 error message for {service_type}: {e}")
 return False

def send_normal_messages(count=5):
 """Send normal messages that should pile up if subscriptions are disabled"""
 
 print(f"\nSending {count} Normal Messages (should pile up if subscriptions disabled)")
 print("-" * 60)
 
 sqs = boto3.client('sqs')
 
 for i in range(count):
 # Bank account message
 bank_customer_id = f"normal-bank-{i+1:03d}-{int(time.time())}"
 bank_message = {
 'customer_id': bank_customer_id,
 'routing_number': '123456789',
 'account_number': f"100123456{i}",
 'message_id': f"normal-bank-{i+1}-{int(time.time())}",
 'message_group_id': bank_customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 
 try:
 sqs.send_message(
 QueueUrl=BANK_ACCOUNT_QUEUE_URL,
 MessageBody=json.dumps(bank_message),
 MessageGroupId=bank_customer_id,
 MessageDeduplicationId=f"normal-bank-{i}-{int(time.time())}"
 )
 print(f" Sent bank message: {bank_customer_id}")
 except Exception as e:
 print(f" Failed bank message: {e}")
 
 # Payment message
 payment_customer_id = f"normal-payment-{i+1:03d}-{int(time.time())}"
 payment_message = {
 'customer_id': payment_customer_id,
 'amount': 50.00 + (i * 10),
 'payment_method': 'bank_account',
 'message_id': f"normal-payment-{i+1}-{int(time.time())}",
 'message_group_id': payment_customer_id,
 'timestamp': datetime.utcnow().isoformat()
 }
 
 try:
 sqs.send_message(
 QueueUrl=PAYMENT_QUEUE_URL,
 MessageBody=json.dumps(payment_message),
 MessageGroupId=payment_customer_id,
 MessageDeduplicationId=f"normal-payment-{i}-{int(time.time())}"
 )
 print(f" Sent payment message: {payment_customer_id}")
 except Exception as e:
 print(f" Failed payment message: {e}")

def send_subscription_control_message(action, service=None):
 """Send subscription control message via SNS"""
 
 print(f"\nSending Subscription Control: {action.upper()}")
 if service:
 print(f" Target Service: {service}")
 print("-" * 40)
 
 sns = boto3.client('sns')
 
 control_message = {
 'action': action,
 'timestamp': datetime.utcnow().isoformat(),
 'source': 'test_script'
 }
 
 if service:
 control_message['service'] = service
 
 try:
 response = sns.publish(
 TopicArn=SUBSCRIPTION_CONTROL_TOPIC_ARN,
 Message=json.dumps(control_message),
 Subject=f'Subscription Control: {action.title()}'
 )
 
 print(f"Control message sent: {response['MessageId']}")
 return True
 
 except Exception as e:
 print(f"Failed to send control message: {e}")
 return False

def wait_and_monitor(duration, description):
 """Wait for a duration while monitoring queue status"""
 
 print(f"\n{description} (monitoring for {duration} seconds)")
 print("-" * 50)
 
 start_time = time.time()
 
 while time.time() - start_time < duration:
 elapsed = int(time.time() - start_time)
 print(f"\nTime: {elapsed}s")
 
 queue_status = check_queue_status()
 
 if elapsed < duration - 5: # Don't sleep on the last iteration
 time.sleep(5)
 
 return queue_status

def main():
 """Main test function"""
 
 print("Testing Subscription Control Flow")
 print("Verify Lambda functions stop processing on 500 errors")
 print("=" * 60)
 
 try:
 # Step 1: Check initial status
 print("\nSTEP 1: Check Initial Status")
 initial_subscription_status = check_subscription_status()
 initial_queue_status = check_queue_status()
 
 # Step 2: Send 500 error messages to trigger subscription disable
 print("\nSTEP 2: Trigger 500 Errors to Disable Subscriptions")
 print("-" * 50)
 
 print("Sending 500 error messages...")
 send_500_error_message('bank-account')
 send_500_error_message('payment')
 
 # Wait for error processing
 print("\nWaiting for error processing and subscription disable...")
 time.sleep(10)
 
 # Check subscription status after errors
 print("\nChecking subscription status after 500 errors...")
 post_error_subscription_status = check_subscription_status()
 
 # Step 3: Send normal messages (should pile up)
 print("\nSTEP 3: Send Normal Messages (Should Pile Up)")
 send_normal_messages(5)
 
 # Step 4: Monitor message piling up
 print("\nSTEP 4: Monitor Message Accumulation")
 pile_up_status = wait_and_monitor(30, "Waiting for messages to pile up")
 
 # Step 5: Re-enable subscriptions
 print("\nSTEP 5: Re-enable Subscriptions via SNS")
 send_subscription_control_message('enable')
 
 # Wait for control message processing
 print("\nWaiting for subscription re-enable...")
 time.sleep(10)
 
 # Check subscription status after re-enable
 print("\nChecking subscription status after re-enable...")
 final_subscription_status = check_subscription_status()
 
 # Step 6: Monitor message processing
 print("\nSTEP 6: Monitor Message Processing After Re-enable")
 final_status = wait_and_monitor(30, "Waiting for message processing")
 
 # Summary
 print("\nTest Summary")
 print("=" * 30)
 
 print("\nSubscription Status Changes:")
 for service in ['bank-account', 'payment']:
 if service in initial_subscription_status and service in final_subscription_status:
 initial = initial_subscription_status[service]['enabled']
 final = final_subscription_status[service]['enabled']
 print(f" {service.title()}: {initial} → {final}")
 
 print("\nQueue Message Changes:")
 if pile_up_status and final_status:
 for queue in ['bank_account', 'payment']:
 if queue in pile_up_status and queue in final_status:
 pile_up = pile_up_status[queue]['total']
 final = final_status[queue]['total']
 print(f" {queue.replace('_', ' ').title()}: {pile_up} → {final} messages")
 
 print("\nTest Objectives:")
 print(" 500 errors should disable subscriptions")
 print(" Messages should pile up when subscriptions disabled")
 print(" SNS control should re-enable subscriptions")
 print(" Messages should process after re-enable")
 
 except KeyboardInterrupt:
 print("\nTest cancelled by user")
 except Exception as e:
 print(f"\nTest failed: {e}")
 import traceback
 traceback.print_exc()

if __name__ == "__main__":
 main()