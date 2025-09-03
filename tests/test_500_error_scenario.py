#!/usr/bin/env python3
"""
Test 500 Error Scenario
Tests system behavior when Lambda functions encounter server errors (500)
and potentially stop processing messages from SQS queues.

Expected Behavior:
1. Lambda functions encounter 500 errors and retry
2. After multiple failures, Lambda functions may stop subscribing to SQS
3. Messages pile up in the SQS queues
4. System should handle this gracefully without losing messages
"""

import json
import time
import boto3
import uuid
from datetime import datetime
from typing import Dict, Any

# AWS clients
sns_client = boto3.client('sns', region_name='us-east-2')
sqs_client = boto3.client('sqs', region_name='us-east-2')
cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-2')
lambda_client = boto3.client('lambda', region_name='us-east-2')

# Configuration
TRANSACTION_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
BANK_ACCOUNT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo"
PAYMENT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"
BANK_ACCOUNT_LAMBDA_NAME = "utility-customer-system-dev-bank-account-setup"
PAYMENT_LAMBDA_NAME = "utility-customer-system-dev-payment-processing"

def send_bank_account_message(customer_id: str, message_id: str = None) -> str:
 """Send a bank account setup message that will trigger a 500 error"""
 if not message_id:
 message_id = str(uuid.uuid4())
 
 message = {
 "message_id": message_id,
 "customer_id": customer_id,
 "transaction_type": "bank_account_setup",
 "routing_number": "123456789",
 "account_number": "9876543210",
 "account_type": "checking",
 "timestamp": datetime.utcnow().isoformat(),
 "message_group_id": customer_id
 }
 
 response = sns_client.publish(
 TopicArn=TRANSACTION_TOPIC_ARN,
 Message=json.dumps(message),
 MessageGroupId=customer_id,
 MessageDeduplicationId=message_id,
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'bank_account_setup'
 }
 }
 )
 
 return response['MessageId']

def send_payment_message(customer_id: str, amount: float = 150.00, message_id: str = None) -> str:
 """Send a payment message that will trigger a 500 error"""
 if not message_id:
 message_id = str(uuid.uuid4())
 
 message = {
 "message_id": message_id,
 "customer_id": customer_id,
 "transaction_type": "payment",
 "amount": amount,
 "payment_method": "bank_account",
 "description": "Monthly utility bill",
 "timestamp": datetime.utcnow().isoformat(),
 "message_group_id": customer_id
 }
 
 response = sns_client.publish(
 TopicArn=TRANSACTION_TOPIC_ARN,
 Message=json.dumps(message),
 MessageGroupId=customer_id,
 MessageDeduplicationId=message_id,
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'payment'
 }
 }
 )
 
 return response['MessageId']

def get_queue_attributes(queue_url: str) -> Dict[str, Any]:
 """Get queue attributes including message counts"""
 response = sqs_client.get_queue_attributes(
 QueueUrl=queue_url,
 AttributeNames=[
 'ApproximateNumberOfMessages',
 'ApproximateNumberOfMessagesNotVisible',
 'ApproximateNumberOfMessagesDelayed'
 ]
 )
 return response['Attributes']

def get_lambda_metrics(function_name: str, start_time: datetime, end_time: datetime) -> Dict[str, float]:
 """Get Lambda function metrics from CloudWatch"""
 
 # Get invocations
 invocations_response = cloudwatch_client.get_metric_statistics(
 Namespace='AWS/Lambda',
 MetricName='Invocations',
 Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
 StartTime=start_time,
 EndTime=end_time,
 Period=300,
 Statistics=['Sum']
 )
 
 # Get errors
 errors_response = cloudwatch_client.get_metric_statistics(
 Namespace='AWS/Lambda',
 MetricName='Errors',
 Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
 StartTime=start_time,
 EndTime=end_time,
 Period=300,
 Statistics=['Sum']
 )
 
 # Get throttles
 throttles_response = cloudwatch_client.get_metric_statistics(
 Namespace='AWS/Lambda',
 MetricName='Throttles',
 Dimensions=[{'Name': 'FunctionName', 'Value': function_name}],
 StartTime=start_time,
 EndTime=end_time,
 Period=300,
 Statistics=['Sum']
 )
 
 invocations = sum([point['Sum'] for point in invocations_response['Datapoints']])
 errors = sum([point['Sum'] for point in errors_response['Datapoints']])
 throttles = sum([point['Sum'] for point in throttles_response['Datapoints']])
 
 return {
 'invocations': invocations,
 'errors': errors,
 'throttles': throttles
 }

def get_event_source_mapping_status(function_name: str) -> Dict[str, Any]:
 """Get the status of event source mappings for a Lambda function"""
 response = lambda_client.list_event_source_mappings(FunctionName=function_name)
 
 mappings = []
 for mapping in response['EventSourceMappings']:
 mappings.append({
 'uuid': mapping['UUID'],
 'state': mapping['State'],
 'state_transition_reason': mapping.get('StateTransitionReason', ''),
 'last_modified': mapping['LastModified'],
 'batch_size': mapping['BatchSize']
 })
 
 return mappings

def main():
 print("🧪 500 ERROR SCENARIO TEST")
 print("=" * 50)
 
 # Test customers that will trigger 500 errors
 error_customers = [
 "CUST-ERROR500-BANK-1",
 "CUST-ERROR500-BANK-2", 
 "CUST-ERROR500-PAYMENT-1",
 "CUST-ERROR500-PAYMENT-2"
 ]
 
 print("\n1. Getting initial queue states...")
 initial_bank_attrs = get_queue_attributes(BANK_ACCOUNT_QUEUE_URL)
 initial_payment_attrs = get_queue_attributes(PAYMENT_QUEUE_URL)
 
 print(f" Bank Account Queue - Messages: {initial_bank_attrs['ApproximateNumberOfMessages']}")
 print(f" Payment Queue - Messages: {initial_payment_attrs['ApproximateNumberOfMessages']}")
 
 print("\n2. Checking initial Lambda event source mapping status...")
 bank_mappings = get_event_source_mapping_status(BANK_ACCOUNT_LAMBDA_NAME)
 payment_mappings = get_event_source_mapping_status(PAYMENT_LAMBDA_NAME)
 
 print(f" Bank Account Lambda mappings: {len(bank_mappings)}")
 for mapping in bank_mappings:
 print(f" - State: {mapping['state']}, UUID: {mapping['uuid'][:8]}...")
 
 print(f" Payment Lambda mappings: {len(payment_mappings)}")
 for mapping in payment_mappings:
 print(f" - State: {mapping['state']}, UUID: {mapping['uuid'][:8]}...")
 
 print("\n3. Sending messages that will trigger 500 errors...")
 
 # Send bank account messages that will cause 500 errors
 bank_message_ids = []
 for customer in error_customers[:2]: # First 2 customers for bank account errors
 print(f" Sending bank account setup for {customer} (will trigger 500 error)...")
 message_id = send_bank_account_message(customer)
 bank_message_ids.append(message_id)
 print(f" Bank account message sent: {message_id}")
 time.sleep(1) # Small delay between messages
 
 # Send payment messages that will cause 500 errors
 payment_message_ids = []
 for customer in error_customers[2:]: # Last 2 customers for payment errors
 print(f" Sending payment for {customer} (will trigger 500 error)...")
 message_id = send_payment_message(customer, 200.00)
 payment_message_ids.append(message_id)
 print(f" Payment message sent: {message_id}")
 time.sleep(1) # Small delay between messages
 
 print("\n4. Sending additional messages to test queue buildup...")
 
 # Send more messages to see if they pile up
 additional_customers = [
 "CUST-ERROR500-BANK-3",
 "CUST-ERROR500-BANK-4",
 "CUST-ERROR500-PAYMENT-3", 
 "CUST-ERROR500-PAYMENT-4"
 ]
 
 for customer in additional_customers[:2]:
 send_bank_account_message(customer)
 print(f" Additional bank account message sent for {customer}")
 time.sleep(0.5)
 
 for customer in additional_customers[2:]:
 send_payment_message(customer, 175.00)
 print(f" Additional payment message sent for {customer}")
 time.sleep(0.5)
 
 print("\n5. Waiting 60 seconds for processing and potential failures...")
 time.sleep(60)
 
 print("\n6. Checking Lambda invocations and errors...")
 end_time = datetime.utcnow()
 start_time = datetime.utcnow().replace(minute=max(0, end_time.minute-10))
 
 bank_metrics = get_lambda_metrics(BANK_ACCOUNT_LAMBDA_NAME, start_time, end_time)
 payment_metrics = get_lambda_metrics(PAYMENT_LAMBDA_NAME, start_time, end_time)
 
 print(f" Bank Account Lambda:")
 print(f" - Invocations: {bank_metrics['invocations']}")
 print(f" - Errors: {bank_metrics['errors']}")
 print(f" - Throttles: {bank_metrics['throttles']}")
 
 print(f" Payment Lambda:")
 print(f" - Invocations: {payment_metrics['invocations']}")
 print(f" - Errors: {payment_metrics['errors']}")
 print(f" - Throttles: {payment_metrics['throttles']}")
 
 print("\n7. Checking queue states after processing...")
 final_bank_attrs = get_queue_attributes(BANK_ACCOUNT_QUEUE_URL)
 final_payment_attrs = get_queue_attributes(PAYMENT_QUEUE_URL)
 
 print(f" Bank Account Queue:")
 print(f" - Messages: {final_bank_attrs['ApproximateNumberOfMessages']}")
 print(f" - Messages Not Visible: {final_bank_attrs['ApproximateNumberOfMessagesNotVisible']}")
 print(f" - Messages Delayed: {final_bank_attrs['ApproximateNumberOfMessagesDelayed']}")
 
 print(f" Payment Queue:")
 print(f" - Messages: {final_payment_attrs['ApproximateNumberOfMessages']}")
 print(f" - Messages Not Visible: {final_payment_attrs['ApproximateNumberOfMessagesNotVisible']}")
 print(f" - Messages Delayed: {final_payment_attrs['ApproximateNumberOfMessagesDelayed']}")
 
 print("\n8. Checking Lambda event source mapping status after errors...")
 final_bank_mappings = get_event_source_mapping_status(BANK_ACCOUNT_LAMBDA_NAME)
 final_payment_mappings = get_event_source_mapping_status(PAYMENT_LAMBDA_NAME)
 
 print(f" Bank Account Lambda mappings:")
 for mapping in final_bank_mappings:
 print(f" - State: {mapping['state']}, Reason: {mapping['state_transition_reason']}")
 
 print(f" Payment Lambda mappings:")
 for mapping in final_payment_mappings:
 print(f" - State: {mapping['state']}, Reason: {mapping['state_transition_reason']}")
 
 print("\n9. Waiting additional 30 seconds to see if more messages pile up...")
 time.sleep(30)
 
 # Check queue states again
 later_bank_attrs = get_queue_attributes(BANK_ACCOUNT_QUEUE_URL)
 later_payment_attrs = get_queue_attributes(PAYMENT_QUEUE_URL)
 
 print(f" Bank Account Queue (after additional wait):")
 print(f" - Messages: {later_bank_attrs['ApproximateNumberOfMessages']}")
 
 print(f" Payment Queue (after additional wait):")
 print(f" - Messages: {later_payment_attrs['ApproximateNumberOfMessages']}")
 
 print("\nTest completed!")
 print("\nExpected results:")
 print("- Lambda functions should encounter 500 errors and retry")
 print("- After multiple failures, event source mappings may be disabled")
 print("- Messages should pile up in SQS queues when Lambdas stop processing")
 print("- System should handle this gracefully without losing messages")
 
 # Summary
 print(f"\nSUMMARY:")
 print(f"Bank Account Lambda - Errors: {bank_metrics['errors']}/{bank_metrics['invocations']} invocations")
 print(f"Payment Lambda - Errors: {payment_metrics['errors']}/{payment_metrics['invocations']} invocations")
 print(f"Bank Queue Messages: {initial_bank_attrs['ApproximateNumberOfMessages']} → {later_bank_attrs['ApproximateNumberOfMessages']}")
 print(f"Payment Queue Messages: {initial_payment_attrs['ApproximateNumberOfMessages']} → {later_payment_attrs['ApproximateNumberOfMessages']}")

if __name__ == "__main__":
 main()