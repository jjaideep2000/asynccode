#!/usr/bin/env python3
"""
Simple test for 400 error scenario
"""

import json
import boto3
import time
import uuid
from datetime import datetime

def main():
 # Load outputs
 with open('../deploy/outputs_simple.json', 'r') as f:
 outputs = json.load(f)
 
 sns_client = boto3.client('sns', region_name=outputs['region'])
 
 print("🧪 SIMPLE 400 ERROR TEST")
 print("=" * 30)
 
 # Customer that will trigger 400 error
 customer_id = "CUST-ERROR400-SIMPLE"
 
 # Step 1: Send bank account setup (will trigger 400 error)
 print(f"\n1. Sending bank account setup for {customer_id} (will trigger 400 error)...")
 
 bank_message = {
 "message_id": f"bank-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:8]}",
 "transaction_type": "bank_account_setup",
 "customer_id": customer_id,
 "message_group_id": customer_id,
 "timestamp": datetime.utcnow().isoformat(),
 "transaction_id": str(uuid.uuid4()),
 "routing_number": "123456789",
 "account_number": "INVALID_FORMAT", # This triggers 400 error
 "account_type": "checking"
 }
 
 bank_response = sns_client.publish(
 TopicArn=outputs['transaction_processing_topic_arn'],
 Message=json.dumps(bank_message),
 Subject="Transaction: bank_account_setup",
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'bank_account_setup'
 },
 'customer_id': {
 'DataType': 'String', 
 'StringValue': customer_id
 }
 },
 MessageGroupId=customer_id,
 MessageDeduplicationId=bank_message["message_id"]
 )
 
 print(f" Bank account message sent: {bank_response['MessageId']}")
 
 # Step 2: Send payment (should work fine)
 print(f"\n2. Sending payment for {customer_id} (should work fine)...")
 
 payment_message = {
 "message_id": f"payment-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:8]}",
 "transaction_type": "payment",
 "customer_id": customer_id,
 "message_group_id": customer_id,
 "timestamp": datetime.utcnow().isoformat(),
 "transaction_id": str(uuid.uuid4()),
 "amount": 150.00,
 "payment_method": "bank_account",
 "bill_type": "utility",
 "due_date": "2025-09-15"
 }
 
 payment_response = sns_client.publish(
 TopicArn=outputs['transaction_processing_topic_arn'],
 Message=json.dumps(payment_message),
 Subject="Transaction: payment",
 MessageAttributes={
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'payment'
 },
 'customer_id': {
 'DataType': 'String', 
 'StringValue': customer_id
 }
 },
 MessageGroupId=customer_id,
 MessageDeduplicationId=payment_message["message_id"]
 )
 
 print(f" Payment message sent: {payment_response['MessageId']}")
 
 # Step 3: Wait and check results
 print(f"\n3. Waiting 30 seconds for processing...")
 time.sleep(30)
 
 # Step 4: Check Lambda metrics
 print(f"\n4. Checking Lambda invocations...")
 
 cloudwatch = boto3.client('cloudwatch', region_name=outputs['region'])
 
 # Check bank account Lambda invocations
 try:
 end_time = datetime.utcnow()
 start_time = datetime.utcnow().replace(minute=max(0, end_time.minute-5))
 
 bank_response = cloudwatch.get_metric_statistics(
 Namespace='AWS/Lambda',
 MetricName='Invocations',
 Dimensions=[{'Name': 'FunctionName', 'Value': outputs['bank_account_lambda_name']}],
 StartTime=start_time,
 EndTime=end_time,
 Period=300,
 Statistics=['Sum']
 )
 
 payment_response = cloudwatch.get_metric_statistics(
 Namespace='AWS/Lambda',
 MetricName='Invocations',
 Dimensions=[{'Name': 'FunctionName', 'Value': outputs['payment_lambda_name']}],
 StartTime=start_time,
 EndTime=end_time,
 Period=300,
 Statistics=['Sum']
 )
 
 bank_invocations = sum(dp['Sum'] for dp in bank_response['Datapoints'])
 payment_invocations = sum(dp['Sum'] for dp in payment_response['Datapoints'])
 
 print(f" Bank Account Lambda invocations: {bank_invocations}")
 print(f" Payment Lambda invocations: {payment_invocations}")
 
 # Check for errors
 bank_errors_response = cloudwatch.get_metric_statistics(
 Namespace='AWS/Lambda',
 MetricName='Errors',
 Dimensions=[{'Name': 'FunctionName', 'Value': outputs['bank_account_lambda_name']}],
 StartTime=start_time,
 EndTime=end_time,
 Period=300,
 Statistics=['Sum']
 )
 
 bank_errors = sum(dp['Sum'] for dp in bank_errors_response['Datapoints'])
 print(f" Bank Account Lambda errors: {bank_errors}")
 
 except Exception as e:
 print(f" Error checking metrics: {e}")
 
 # Step 5: Check logs
 print(f"\n5. Checking recent Lambda logs...")
 
 logs_client = boto3.client('logs', region_name=outputs['region'])
 
 try:
 # Check bank account logs
 bank_log_response = logs_client.filter_log_events(
 logGroupName=f"/aws/lambda/{outputs['bank_account_lambda_name']}",
 startTime=int((datetime.utcnow().timestamp() - 300) * 1000),
 limit=10
 )
 
 print(f" Bank Account Lambda recent logs ({len(bank_log_response['events'])} events):")
 for event in bank_log_response['events'][-5:]:
 timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
 print(f" {timestamp.strftime('%H:%M:%S')}: {event['message'].strip()}")
 
 # Check payment logs
 payment_log_response = logs_client.filter_log_events(
 logGroupName=f"/aws/lambda/{outputs['payment_lambda_name']}",
 startTime=int((datetime.utcnow().timestamp() - 300) * 1000),
 limit=10
 )
 
 print(f"\n Payment Lambda recent logs ({len(payment_log_response['events'])} events):")
 for event in payment_log_response['events'][-5:]:
 timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
 print(f" {timestamp.strftime('%H:%M:%S')}: {event['message'].strip()}")
 
 except Exception as e:
 print(f" Error checking logs: {e}")
 
 print(f"\nTest completed!")
 print(f"Expected results:")
 print(f"- Bank account Lambda should be invoked and handle 400 error gracefully")
 print(f"- Payment Lambda should be invoked and process successfully")
 print(f"- Both Lambdas should continue processing (not stop subscription)")
 print(f"- OpenTelemetry should capture error telemetry")

if __name__ == "__main__":
 main()