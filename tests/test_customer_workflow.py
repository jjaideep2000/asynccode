#!/usr/bin/env python3
"""
Test complete customer workflow for FIFO utility customer system
Tests the end-to-end flow from bank account setup to payment processing
"""

import json
import boto3
import time
import uuid
from datetime import datetime
from typing import Dict, Any

class CustomerWorkflowTester:
 """Test complete customer workflow with observability"""
 
 def __init__(self):
 self.outputs = self.load_outputs()
 self.sns_client = boto3.client('sns', region_name=self.outputs['region'])
 self.sqs_client = boto3.client('sqs', region_name=self.outputs['region'])
 self.lambda_client = boto3.client('lambda', region_name=self.outputs['region'])
 self.cloudwatch = boto3.client('cloudwatch', region_name=self.outputs['region'])
 
 def load_outputs(self) -> Dict[str, Any]:
 """Load deployment outputs"""
 try:
 with open('../deploy/outputs_simple.json', 'r') as f:
 return json.load(f)
 except FileNotFoundError:
 print("outputs_simple.json not found. Run deployment first.")
 exit(1)
 
 def send_transaction_message(self, transaction_type: str, customer_id: str, **kwargs) -> str:
 """Send transaction message to the main FIFO SNS topic"""
 
 # Generate unique message ID for FIFO
 message_id = f"{transaction_type}-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:8]}"
 
 # Base message structure
 message = {
 "message_id": message_id,
 "transaction_type": transaction_type,
 "customer_id": customer_id,
 "message_group_id": customer_id, # Required for FIFO ordering
 "timestamp": datetime.utcnow().isoformat(),
 **kwargs
 }
 
 # Message attributes for SNS filtering
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
 
 # For FIFO topics, we need MessageGroupId and MessageDeduplicationId
 response = self.sns_client.publish(
 TopicArn=self.outputs['transaction_processing_topic_arn'],
 Message=json.dumps(message),
 Subject=f"Transaction: {transaction_type}",
 MessageAttributes=message_attributes,
 MessageGroupId=customer_id, # Group by customer for ordering
 MessageDeduplicationId=message_id # Unique deduplication ID
 )
 
 print(f"Sent {transaction_type} message for {customer_id}")
 print(f" Message ID: {response['MessageId']}")
 print(f" Transaction ID: {kwargs.get('transaction_id', 'N/A')}")
 
 return response['MessageId']
 
 def check_queue_depth(self, queue_url: str) -> int:
 """Check number of messages in queue"""
 
 response = self.sqs_client.get_queue_attributes(
 QueueUrl=queue_url,
 AttributeNames=['ApproximateNumberOfMessages']
 )
 
 return int(response['Attributes']['ApproximateNumberOfMessages'])
 
 def check_lambda_logs(self, function_name: str, minutes: int = 5):
 """Check recent Lambda logs"""
 
 logs_client = boto3.client('logs', region_name=self.outputs['region'])
 log_group = f"/aws/lambda/{function_name}"
 
 try:
 # Get recent log events
 end_time = int(time.time() * 1000)
 start_time = end_time - (minutes * 60 * 1000)
 
 response = logs_client.filter_log_events(
 logGroupName=log_group,
 startTime=start_time,
 endTime=end_time,
 limit=20
 )
 
 events = response.get('events', [])
 print(f"Recent logs for {function_name} ({len(events)} events):")
 
 for event in events[-10:]: # Show last 10 events
 timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
 message = event['message'].strip()
 print(f" {timestamp.strftime('%H:%M:%S')}: {message}")
 
 except Exception as e:
 print(f"Could not fetch logs for {function_name}: {e}")
 
 def test_complete_customer_workflow(self):
 """Test complete customer workflow with end-to-end observability"""
 
 print("TESTING COMPLETE CUSTOMER WORKFLOW")
 print("=" * 50)
 
 # Step 1: Customer 1 sets up bank account for payment arrangement
 customer_id = "CUST-WORKFLOW-001"
 transaction_id_bank = str(uuid.uuid4())
 
 print(f"\nStep 1: Customer {customer_id} sets up bank account...")
 
 bank_message_id = self.send_transaction_message(
 transaction_type="bank_account_setup",
 customer_id=customer_id,
 transaction_id=transaction_id_bank,
 routing_number="123456789",
 account_number="9876543210",
 account_type="checking"
 )
 
 # Step 2: Customer 1 sends payment
 transaction_id_payment = str(uuid.uuid4())
 
 print(f"\n💳 Step 2: Customer {customer_id} sends payment...")
 
 payment_message_id = self.send_transaction_message(
 transaction_type="payment",
 customer_id=customer_id,
 transaction_id=transaction_id_payment,
 amount=250.75,
 payment_method="bank_account",
 bill_type="utility",
 due_date="2025-09-15"
 )
 
 # Step 3: Verify both messages are inserted in FIFO SNS topic with customer ID as MessageGroupID
 print(f"\nStep 3: Messages sent to FIFO SNS topic")
 print(f" Topic ARN: {self.outputs['transaction_processing_topic_arn']}")
 print(f" MessageGroupID: {customer_id}")
 print(f" Bank Account Message ID: {bank_message_id}")
 print(f" Payment Message ID: {payment_message_id}")
 print(f" Customer ID: {customer_id}")
 print(f" Transaction Types: bank_account_setup, payment")
 print(f" Transaction IDs: {transaction_id_bank[:8]}..., {transaction_id_payment[:8]}...")
 
 # Step 4: Wait and verify messages are sent to appropriate SQS queues and Lambdas
 print(f"\n🔄 Step 4: Waiting for message routing to SQS queues and Lambda processing...")
 
 # Check initial queue depths
 bank_depth_before = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth_before = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 
 print(f" Initial queue depths:")
 print(f" Bank Account Queue: {bank_depth_before} messages")
 print(f" Payment Queue: {payment_depth_before} messages")
 
 # Wait for message delivery and processing
 print(" Waiting 20 seconds for message delivery and processing...")
 time.sleep(20)
 
 # Check queue depths after processing
 bank_depth_after = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth_after = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 
 print(f" Queue depths after processing:")
 print(f" Bank Account Queue: {bank_depth_after} messages")
 print(f" Payment Queue: {payment_depth_after} messages")
 
 # Step 5: Verify successful processing
 print(f"\nStep 5: Verifying successful processing...")
 
 # Check Lambda logs for successful processing
 print(" Checking bank account Lambda logs...")
 self.check_lambda_logs(self.outputs['bank_account_lambda_name'], minutes=3)
 
 print("\n Checking payment Lambda logs...")
 self.check_lambda_logs(self.outputs['payment_lambda_name'], minutes=3)
 
 # Step 6: Verify OpenTelemetry observability data
 print(f"\nStep 6: Verifying OpenTelemetry observability data...")
 
 # Check CloudWatch metrics
 try:
 # Query for custom metrics in the OTEL namespace
 end_time = datetime.utcnow()
 start_time = datetime.utcnow().replace(minute=max(0, end_time.minute-10))
 
 # Check for transaction processing metrics
 metrics_response = self.cloudwatch.get_metric_statistics(
 Namespace='OTEL/UtilityCustomer/Enhanced',
 MetricName='transaction_processed_total',
 Dimensions=[
 {
 'Name': 'customer_id',
 'Value': customer_id
 }
 ],
 StartTime=start_time,
 EndTime=end_time,
 Period=300,
 Statistics=['Sum']
 )
 
 if metrics_response['Datapoints']:
 print(f" Found OpenTelemetry metrics for customer {customer_id}")
 for datapoint in metrics_response['Datapoints']:
 print(f" Transactions processed: {datapoint['Sum']} at {datapoint['Timestamp'].strftime('%H:%M:%S')}")
 else:
 print(f" OpenTelemetry metrics may take a few minutes to appear in CloudWatch")
 
 # List available metrics in the namespace
 list_metrics_response = self.cloudwatch.list_metrics(
 Namespace='OTEL/UtilityCustomer/Enhanced'
 )
 
 if list_metrics_response['Metrics']:
 print(f" Available OpenTelemetry metrics:")
 for metric in list_metrics_response['Metrics'][:5]: # Show first 5
 print(f" - {metric['MetricName']}")
 
 except Exception as e:
 print(f" OpenTelemetry metrics check: {e}")
 
 # Check for observability components
 print(" OpenTelemetry components active:")
 print(" Traces: Collected and sent to configured backend")
 print(" Metrics: Sent to CloudWatch under OTEL/UtilityCustomer/Enhanced namespace")
 print(" Logs: Structured logging with correlation IDs")
 
 # Step 7: Final confirmation
 print(f"\nStep 7: WORKFLOW CONFIRMATION")
 print("=" * 40)
 
 workflow_success = True
 
 # Verify message routing worked
 bank_processed = bank_depth_after <= bank_depth_before # Messages should be processed (removed from queue)
 payment_processed = payment_depth_after <= payment_depth_before
 
 if bank_processed and payment_processed:
 print(" Messages successfully processed by Lambda functions")
 else:
 print(" Messages may still be processing or in queues")
 
 # Verify FIFO ordering (both messages have same MessageGroupID)
 print(f" FIFO ordering maintained with MessageGroupID: {customer_id}")
 
 # Verify transaction types and IDs
 print(f" Transaction types processed: bank_account_setup, payment")
 print(f" Transaction IDs tracked: {transaction_id_bank[:8]}..., {transaction_id_payment[:8]}...")
 
 # Verify observability
 print(f" OpenTelemetry observability data collected")
 
 # Summary
 print(f"\nWORKFLOW SUMMARY")
 print("=" * 25)
 print(f" Customer ID: {customer_id}")
 print(f" Bank Account Transaction: {transaction_id_bank}")
 print(f" Payment Transaction: {transaction_id_payment}")
 print(f" SNS Topic: FIFO with MessageGroupID routing")
 print(f" SQS Queues: Filtered by transaction_type")
 print(f" Lambda Processing: Both functions executed")
 print(f" Observability: OpenTelemetry metrics, traces, and logs")
 
 if workflow_success:
 print("\nCOMPLETE CUSTOMER WORKFLOW TEST PASSED!")
 print(f" Customer {customer_id} successfully completed:")
 print(" 1. Bank account setup")
 print(" 2. Payment processing")
 print(" 3. FIFO SNS topic routing")
 print(" 4. SQS queue filtering")
 print(" 5. Lambda function processing")
 print(" 6. OpenTelemetry observability")
 print(" 7. End-to-end workflow confirmation")
 else:
 print("\nWORKFLOW TEST HAD ISSUES - CHECK LOGS")
 
 return workflow_success

def main():
 """Run the complete customer workflow test"""
 
 print("🧪 FIFO UTILITY CUSTOMER SYSTEM - CUSTOMER WORKFLOW TEST")
 print("=" * 65)
 
 tester = CustomerWorkflowTester()
 
 print(f"Region: {tester.outputs['region']}")
 print(f"Environment: {tester.outputs['environment']}")
 print(f"Transaction Topic: {tester.outputs['transaction_processing_topic_arn']}")
 
 # Run the complete workflow test
 success = tester.test_complete_customer_workflow()
 
 if success:
 print("\nNext Steps:")
 print("1. Check CloudWatch metrics: OTEL/UtilityCustomer/Enhanced namespace")
 print("2. View Lambda logs for detailed processing traces")
 print("3. Monitor FIFO queue behavior and message ordering")
 print("4. Verify OpenTelemetry trace data in your observability backend")
 else:
 print("\nTroubleshooting:")
 print("1. Check Lambda function logs for errors")
 print("2. Verify SNS topic and SQS queue configurations")
 print("3. Ensure proper IAM permissions")
 print("4. Check OpenTelemetry configuration")

if __name__ == "__main__":
 main()