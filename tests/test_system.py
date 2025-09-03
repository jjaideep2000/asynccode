#!/usr/bin/env python3
"""
Test the utility customer system end-to-end
"""

import json
import boto3
import time
import random
from datetime import datetime
from typing import Dict, Any

class UtilitySystemTester:
 """Test the complete utility customer system"""
 
 def __init__(self):
 self.outputs = self.load_outputs()
 self.sns_client = boto3.client('sns', region_name=self.outputs['region'])
 self.sqs_client = boto3.client('sqs', region_name=self.outputs['region'])
 self.lambda_client = boto3.client('lambda', region_name=self.outputs['region'])
 self.cloudwatch = boto3.client('cloudwatch', region_name=self.outputs['region'])
 
 def load_outputs(self) -> Dict[str, Any]:
 """Load deployment outputs"""
 try:
 with open('../deploy/outputs.json', 'r') as f:
 return json.load(f)
 except FileNotFoundError:
 print("outputs.json not found. Run deployment first.")
 exit(1)
 
 def send_bank_account_message(self, customer_id: str) -> str:
 """Send bank account setup message"""
 
 message = {
 "message_id": f"bank-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}",
 "customer_id": customer_id,
 "routing_number": f"{random.randint(100000000, 999999999)}",
 "account_number": f"{random.randint(1000000000, 9999999999)}",
 "account_type": "checking",
 "timestamp": datetime.utcnow().isoformat()
 }
 
 response = self.sns_client.publish(
 TopicArn=self.outputs['bank_account_topic_arn'],
 Message=json.dumps(message),
 Subject="Bank Account Setup Request"
 )
 
 print(f"Sent bank account setup: {customer_id}")
 return response['MessageId']
 
 def send_payment_message(self, customer_id: str, amount: float) -> str:
 """Send payment processing message"""
 
 message = {
 "message_id": f"pay-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}",
 "customer_id": customer_id,
 "amount": amount,
 "payment_method": "bank_account",
 "bill_type": "utility",
 "due_date": "2025-09-15",
 "timestamp": datetime.utcnow().isoformat()
 }
 
 response = self.sns_client.publish(
 TopicArn=self.outputs['payment_topic_arn'],
 Message=json.dumps(message),
 Subject="Payment Processing Request"
 )
 
 print(f"Sent payment: {customer_id} - ${amount}")
 return response['MessageId']
 
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
 
 def check_cloudwatch_metrics(self):
 """Check CloudWatch metrics"""
 
 print("\nChecking CloudWatch metrics...")
 
 try:
 # List metrics in our namespace
 response = self.cloudwatch.list_metrics(
 Namespace='OTEL/UtilityCustomer/Enhanced'
 )
 
 metrics = response.get('Metrics', [])
 print(f"Found {len(metrics)} metrics in OTEL namespace")
 
 # Show unique metric names
 metric_names = set(m['MetricName'] for m in metrics)
 for name in sorted(metric_names):
 print(f" - {name}")
 
 except Exception as e:
 print(f"Could not fetch metrics: {e}")
 
 def test_happy_path(self):
 """Test happy path scenarios"""
 
 print("\nTESTING HAPPY PATH")
 print("=" * 40)
 
 customers = [
 "CUST-001-PREMIUM",
 "CUST-002-STANDARD",
 "CUST-003-ENTERPRISE"
 ]
 
 # Send bank account setup messages
 for customer in customers:
 self.send_bank_account_message(customer)
 
 # Send payment messages
 for customer in customers:
 amount = random.uniform(100, 500)
 self.send_payment_message(customer, round(amount, 2))
 
 print(f"Sent {len(customers) * 2} happy path messages")
 
 def test_error_scenarios(self):
 """Test error handling scenarios"""
 
 print("\nTESTING ERROR SCENARIOS")
 print("=" * 40)
 
 # Test 400 errors (should continue processing)
 print("Testing 400 errors...")
 self.send_bank_account_message("CUST-ERROR400-BANK")
 self.send_payment_message("CUST-ERROR400-PAY", 150.00)
 
 # Test 500 errors (should stop subscription)
 print("Testing 500 errors...")
 self.send_bank_account_message("CUST-ERROR500-BANK")
 self.send_payment_message("CUST-ERROR500-PAY", 200.00)
 
 print("Sent error scenario messages")
 
 def test_subscription_control(self):
 """Test subscription control functionality"""
 
 print("\nTESTING SUBSCRIPTION CONTROL")
 print("=" * 40)
 
 # Stop all subscriptions
 self.send_subscription_control("stop")
 
 # Wait a moment
 time.sleep(2)
 
 # Send some messages (should pile up in queues)
 print("Sending messages while subscriptions are stopped...")
 self.send_bank_account_message("CUST-PILEUP-001")
 self.send_payment_message("CUST-PILEUP-002", 75.00)
 
 # Check queue depths
 time.sleep(5)
 bank_depth = self.check_queue_depth(self.outputs['bank_account_queue_url'])
 payment_depth = self.check_queue_depth(self.outputs['payment_queue_url'])
 
 print(f"Queue depths: Bank={bank_depth}, Payment={payment_depth}")
 
 # Restart subscriptions
 self.send_subscription_control("start")
 
 print("Subscription control test completed")
 
 def run_comprehensive_test(self):
 """Run comprehensive system test"""
 
 print("🧪 UTILITY CUSTOMER SYSTEM - COMPREHENSIVE TEST")
 print("=" * 60)
 
 print(f"Region: {self.outputs['region']}")
 print(f"Environment: {self.outputs['environment']}")
 
 # Test scenarios
 self.test_happy_path()
 
 # Wait for processing
 print("\nWaiting for message processing...")
 time.sleep(10)
 
 self.test_error_scenarios()
 
 # Wait for error processing
 print("\nWaiting for error processing...")
 time.sleep(10)
 
 self.test_subscription_control()
 
 # Wait for subscription control
 print("\nWaiting for subscription control...")
 time.sleep(15)
 
 # Check results
 print("\nCHECKING RESULTS")
 print("=" * 30)
 
 # Check Lambda logs
 self.check_lambda_logs(self.outputs['bank_account_lambda_name'])
 self.check_lambda_logs(self.outputs['payment_lambda_name'])
 
 # Check CloudWatch metrics
 self.check_cloudwatch_metrics()
 
 # Final queue check
 print("\nFinal queue status:")
 bank_depth = self.check_queue_depth(self.outputs['bank_account_queue_url'])
 payment_depth = self.check_queue_depth(self.outputs['payment_queue_url'])
 print(f" Bank Account Queue: {bank_depth} messages")
 print(f" Payment Queue: {payment_depth} messages")
 
 print("\nCOMPREHENSIVE TEST COMPLETED!")
 print("\nNext steps:")
 print("1. Check CloudWatch metrics: OTEL/UtilityCustomer/Enhanced namespace")
 print("2. View Lambda logs in CloudWatch")
 print("3. Monitor queue depths and processing")

def main():
 tester = UtilitySystemTester()
 tester.run_comprehensive_test()

if __name__ == "__main__":
 main()