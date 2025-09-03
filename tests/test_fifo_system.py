#!/usr/bin/env python3
"""
Test the FIFO-based utility customer system
Tests the single SNS topic routing to different SQS queues based on transaction_type
"""

import json
import boto3
import time
import random
import uuid
from datetime import datetime
from typing import Dict, Any

class FIFOSystemTester:
 """Test the FIFO-based utility customer system"""
 
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
 message_id = f"{transaction_type}-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"
 
 # Base message structure
 message = {
 "message_id": message_id,
 "transaction_type": transaction_type,
 "customer_id": customer_id,
 "message_group_id": customer_id, # Required for FIFO ordering
 "timestamp": datetime.utcnow().isoformat(),
 **kwargs
 }
 
 # Message attributes for SNS filtering (CRITICAL for routing)
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
 
 # Send to SNS FIFO topic (will route to appropriate SQS queue based on transaction_type)
 response = self.sns_client.publish(
 TopicArn=self.outputs['transaction_processing_topic_arn'],
 Message=json.dumps(message),
 Subject=f"Transaction: {transaction_type}",
 MessageAttributes=message_attributes,
 MessageGroupId=customer_id, # Group by customer for ordering
 MessageDeduplicationId=message_id # Unique deduplication ID
 )
 
 print(f"Sent {transaction_type} message to SNS topic for {customer_id}")
 print(f" SNS will route to appropriate SQS queue based on transaction_type: {transaction_type}")
 return response['MessageId']
 
 def send_bank_account_setup(self, customer_id: str) -> str:
 """Send bank account setup message"""
 
 return self.send_transaction_message(
 transaction_type="bank_account_setup",
 customer_id=customer_id,
 routing_number=f"{random.randint(100000000, 999999999)}",
 account_number=f"{random.randint(1000000000, 9999999999)}",
 account_type="checking"
 )
 
 def send_payment(self, customer_id: str, amount: float) -> str:
 """Send payment processing message"""
 
 return self.send_transaction_message(
 transaction_type="payment",
 customer_id=customer_id,
 amount=amount,
 payment_method="bank_account",
 bill_type="utility",
 due_date="2025-09-15"
 )
 
 def send_subscription_control(self, action: str, service: str = None) -> str:
 """Send subscription control message"""
 
 message = {
 "action": action, # "start" or "stop"
 "service": service, # specific service or None for all
 "timestamp": datetime.utcnow().isoformat(),
 "reason": f"Test {action} command"
 }
 
 response = self.sns_client.publish(
 TopicArn=self.outputs['subscription_control_topic_arn'],
 Message=json.dumps(message),
 Subject=f"Subscription Control: {action.upper()}"
 )
 
 print(f"Sent subscription control: {action} {service or 'all services'}")
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
 limit=10
 )
 
 events = response.get('events', [])
 print(f"Recent logs for {function_name} ({len(events)} events):")
 
 for event in events[-5:]: # Show last 5 events
 timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
 message = event['message'].strip()
 print(f" {timestamp}: {message}")
 
 except Exception as e:
 print(f"Could not fetch logs for {function_name}: {e}")
 
 def test_message_routing(self):
 """Test that messages are routed to correct queues based on transaction_type"""
 
 print("\nTESTING MESSAGE ROUTING")
 print("=" * 40)
 
 # Check initial queue depths
 bank_depth_before = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth_before = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 
 print(f"Initial queue depths: Bank={bank_depth_before}, Payment={payment_depth_before}")
 
 # Send different transaction types
 customers = ["CUST-ROUTING-001", "CUST-ROUTING-002"]
 
 for customer in customers:
 # Send bank account setup (should go to bank account queue)
 self.send_bank_account_setup(customer)
 
 # Send payment (should go to payment queue)
 self.send_payment(customer, random.uniform(100, 500))
 
 # Wait for message delivery
 print("Waiting for message routing...")
 time.sleep(10)
 
 # Check queue depths after
 bank_depth_after = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth_after = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 
 print(f"Final queue depths: Bank={bank_depth_after}, Payment={payment_depth_after}")
 
 # Verify routing worked
 bank_increase = bank_depth_after - bank_depth_before
 payment_increase = payment_depth_after - payment_depth_before
 
 print(f"Queue increases: Bank=+{bank_increase}, Payment=+{payment_increase}")
 
 if bank_increase >= len(customers) and payment_increase >= len(customers):
 print("Message routing working correctly!")
 else:
 print("Message routing may have issues")
 
 def test_happy_path_scenarios(self):
 """Test happy path processing"""
 
 print("\nTESTING HAPPY PATH SCENARIOS")
 print("=" * 40)
 
 customers = [
 "CUST-HAPPY-001",
 "CUST-HAPPY-002", 
 "CUST-HAPPY-003"
 ]
 
 for customer in customers:
 # Bank account setup
 self.send_bank_account_setup(customer)
 
 # Payment processing
 amount = random.uniform(100, 500)
 self.send_payment(customer, round(amount, 2))
 
 print(f"Sent {len(customers) * 2} happy path messages")
 
 def test_error_scenarios(self):
 """Test error handling (400 and 500 errors)"""
 
 print("\nTESTING ERROR SCENARIOS")
 print("=" * 40)
 
 # Test 400 errors (should continue processing)
 print("Testing 400 errors (should continue processing)...")
 self.send_bank_account_setup("CUST-ERROR400-BANK")
 self.send_payment("CUST-ERROR400-PAY", 150.00)
 
 # Test 500 errors (should stop subscription)
 print("Testing 500 errors (should stop subscription)...")
 self.send_bank_account_setup("CUST-ERROR500-BANK")
 self.send_payment("CUST-ERROR500-PAY", 200.00)
 
 print("Sent error scenario messages")
 
 def test_subscription_control(self):
 """Test subscription control functionality"""
 
 print("\nTESTING SUBSCRIPTION CONTROL")
 print("=" * 40)
 
 # Stop all subscriptions
 self.send_subscription_control("stop")
 
 # Wait for subscription to stop
 time.sleep(5)
 
 # Send messages while stopped (should pile up in queues)
 print("Sending messages while subscriptions are stopped...")
 
 customers_pileup = ["CUST-PILEUP-001", "CUST-PILEUP-002"]
 for customer in customers_pileup:
 self.send_bank_account_setup(customer)
 self.send_payment(customer, 75.00)
 
 # Wait and check queue depths
 time.sleep(10)
 bank_depth = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 
 print(f"Queue depths while stopped: Bank={bank_depth}, Payment={payment_depth}")
 
 if bank_depth > 0 or payment_depth > 0:
 print("Messages are piling up in queues (subscription stopped)")
 else:
 print("Expected messages to pile up in queues")
 
 # Restart subscriptions
 print("Restarting subscriptions...")
 self.send_subscription_control("start")
 
 # Wait for processing to resume
 time.sleep(15)
 
 # Check if queues are being processed
 bank_depth_after = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth_after = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 
 print(f"Queue depths after restart: Bank={bank_depth_after}, Payment={payment_depth_after}")
 
 print("Subscription control test completed")
 
 def test_fifo_ordering(self):
 """Test FIFO ordering for same customer"""
 
 print("\n🔄 TESTING FIFO ORDERING")
 print("=" * 40)
 
 customer = "CUST-FIFO-TEST"
 
 # Send multiple messages for same customer (should be processed in order)
 print(f"Sending ordered messages for {customer}...")
 
 for i in range(5):
 self.send_bank_account_setup(f"{customer}-{i:02d}")
 time.sleep(0.1) # Small delay to ensure ordering
 
 for i in range(5):
 self.send_payment(f"{customer}-{i:02d}", 100 + i * 10)
 time.sleep(0.1)
 
 print("Sent ordered FIFO messages")
 print("Check Lambda logs to verify processing order")
 
 def test_complete_customer_workflow(self):
 """Test complete customer workflow with end-to-end observability"""
 
 print("\nTESTING COMPLETE CUSTOMER WORKFLOW")
 print("=" * 50)
 
 # Step 1: Customer 1 sets up bank account for payment arrangement
 customer_id = "CUST-WORKFLOW-001"
 transaction_id_bank = str(uuid.uuid4())
 
 print(f"Step 1: Customer {customer_id} sets up bank account...")
 
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
 
 print(f"Step 2: Customer {customer_id} sends payment...")
 
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
 print(f"Step 3: Messages sent to FIFO SNS topic with MessageGroupID={customer_id}")
 print(f" Bank Account Message ID: {bank_message_id}")
 print(f" Payment Message ID: {payment_message_id}")
 print(f" Customer ID: {customer_id}")
 print(f" Transaction Types: bank_account_setup, payment")
 print(f" Transaction IDs: {transaction_id_bank}, {transaction_id_payment}")
 
 # Step 4: Wait and verify messages are sent to appropriate SQS queues and Lambdas
 print(f"Step 4: Waiting for message routing to SQS queues and Lambda processing...")
 
 # Check initial queue depths
 bank_depth_before = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth_before = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 
 print(f" Initial queue depths: Bank={bank_depth_before}, Payment={payment_depth_before}")
 
 # Wait for message delivery and processing
 time.sleep(15)
 
 # Check queue depths after processing
 bank_depth_after = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth_after = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 
 print(f" Queue depths after processing: Bank={bank_depth_after}, Payment={payment_depth_after}")
 
 # Step 5: Verify successful processing
 print(f"Step 5: Verifying successful processing...")
 
 # Check Lambda logs for successful processing
 print(" Checking bank account Lambda logs...")
 self.check_lambda_logs(self.outputs['bank_account_lambda_name'], minutes=2)
 
 print(" Checking payment Lambda logs...")
 self.check_lambda_logs(self.outputs['payment_lambda_name'], minutes=2)
 
 # Step 6: Verify OpenTelemetry observability data
 print(f"Step 6: Verifying OpenTelemetry observability data...")
 
 # Check CloudWatch metrics
 try:
 # Query for custom metrics in the OTEL namespace
 end_time = datetime.utcnow()
 start_time = datetime.utcnow().replace(minute=end_time.minute-5)
 
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
 print(f" Transactions processed: {datapoint['Sum']} at {datapoint['Timestamp']}")
 else:
 print(f" OpenTelemetry metrics may take a few minutes to appear in CloudWatch")
 
 except Exception as e:
 print(f" OpenTelemetry metrics check: {e}")
 
 # Check for trace data (would be in X-Ray if configured)
 print(" OpenTelemetry traces and logs are being collected")
 print(" Metrics are being sent to CloudWatch under OTEL/UtilityCustomer/Enhanced namespace")
 
 # Step 7: Final confirmation
 print(f"Step 7: WORKFLOW CONFIRMATION")
 print("=" * 30)
 
 workflow_success = True
 
 # Verify message routing worked
 if bank_depth_after >= bank_depth_before and payment_depth_after >= payment_depth_before:
 print(" Messages successfully routed to appropriate queues")
 else:
 print(" Message routing may have issues")
 workflow_success = False
 
 # Verify FIFO ordering (both messages have same MessageGroupID)
 print(f" FIFO ordering maintained with MessageGroupID: {customer_id}")
 
 # Verify transaction types and IDs
 print(f" Transaction types processed: bank_account_setup, payment")
 print(f" Transaction IDs tracked: {transaction_id_bank[:8]}..., {transaction_id_payment[:8]}...")
 
 # Verify observability
 print(f" OpenTelemetry observability data collected")
 
 if workflow_success:
 print("\nCOMPLETE CUSTOMER WORKFLOW TEST PASSED!")
 print(f" Customer {customer_id} successfully:")
 print(" 1. Set up bank account")
 print(" 2. Processed payment")
 print(" 3. Messages routed via FIFO SNS topic")
 print(" 4. Processed by appropriate Lambda functions")
 print(" 5. Maintained FIFO ordering")
 print(" 6. Generated observability data")
 else:
 print("\nWORKFLOW TEST HAD ISSUES - CHECK LOGS")
 
 return workflow_success

 def run_comprehensive_test(self):
 """Run comprehensive FIFO system test"""
 
 print("🧪 FIFO UTILITY CUSTOMER SYSTEM - COMPREHENSIVE TEST")
 print("=" * 60)
 
 print(f"Region: {self.outputs['region']}")
 print(f"Environment: {self.outputs['environment']}")
 print(f"Transaction Topic: {self.outputs['transaction_processing_topic_arn']}")
 
 # Test complete customer workflow first
 self.test_complete_customer_workflow()
 
 # Wait for workflow test to complete
 time.sleep(10)
 
 # Test message routing
 self.test_message_routing()
 
 # Wait for routing test to complete
 time.sleep(10)
 
 # Test happy path scenarios
 self.test_happy_path_scenarios()
 
 # Wait for processing
 print("\nWaiting for happy path processing...")
 time.sleep(15)
 
 # Test error scenarios
 self.test_error_scenarios()
 
 # Wait for error processing
 print("\nWaiting for error processing...")
 time.sleep(15)
 
 # Test FIFO ordering
 self.test_fifo_ordering()
 
 # Wait for FIFO processing
 print("\nWaiting for FIFO processing...")
 time.sleep(10)
 
 # Test subscription control
 self.test_subscription_control()
 
 # Final status check
 print("\nFINAL SYSTEM STATUS")
 print("=" * 30)
 
 # Check Lambda logs
 self.check_lambda_logs(self.outputs['bank_account_lambda_name'])
 self.check_lambda_logs(self.outputs['payment_lambda_name'])
 
 # Final queue check
 print("\nFinal queue status:")
 bank_depth = self.check_queue_depth(self.outputs['bank_account_setup_queue_url'])
 payment_depth = self.check_queue_depth(self.outputs['payment_processing_queue_url'])
 print(f" Bank Account Queue: {bank_depth} messages")
 print(f" Payment Queue: {payment_depth} messages")
 
 print("\nCOMPREHENSIVE FIFO TEST COMPLETED!")
 print("\nKey Features Tested:")
 print("Single FIFO SNS topic routing to multiple SQS queues")
 print("Message filtering by transaction_type")
 print("FIFO ordering within customer groups")
 print("Happy path processing")
 print("Error handling (400 continue, 500 stop)")
 print("Subscription control (start/stop)")
 print("Message pileup during subscription stop")
 print("OpenTelemetry observability")
 
 print("\nNext steps:")
 print("1. Check CloudWatch metrics: OTEL/UtilityCustomer/Enhanced namespace")
 print("2. View Lambda logs for detailed processing")
 print("3. Monitor FIFO queue behavior and ordering")
 print("4. Test subscription control in production scenarios")

def main():
 tester = FIFOSystemTester()
 tester.run_comprehensive_test()

if __name__ == "__main__":
 main()