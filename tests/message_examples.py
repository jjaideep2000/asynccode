#!/usr/bin/env python3
"""
Example message structures for the FIFO utility customer system
"""

import json
from datetime import datetime

def bank_account_setup_message():
 """Example bank account setup message"""
 return {
 "message_id": "bank-1724932800-1234",
 "transaction_type": "bank_account_setup",
 "customer_id": "CUST-001-PREMIUM",
 "message_group_id": "CUST-001-PREMIUM", # Required for FIFO ordering
 "routing_number": "123456789",
 "account_number": "9876543210",
 "account_type": "checking",
 "timestamp": datetime.utcnow().isoformat()
 }

def payment_message():
 """Example payment processing message"""
 return {
 "message_id": "pay-1724932800-5678",
 "transaction_type": "payment",
 "customer_id": "CUST-001-PREMIUM",
 "message_group_id": "CUST-001-PREMIUM", # Required for FIFO ordering
 "amount": 150.75,
 "payment_method": "bank_account",
 "bill_type": "utility",
 "due_date": "2025-09-15",
 "timestamp": datetime.utcnow().isoformat()
 }

def subscription_control_message():
 """Example subscription control message"""
 return {
 "action": "stop", # or "start"
 "service": "bank-account-setup", # or "payment-processing" or None for all
 "timestamp": datetime.utcnow().isoformat(),
 "reason": "Service maintenance"
 }

def sns_message_attributes():
 """Example SNS message attributes for filtering"""
 return {
 'transaction_type': {
 'DataType': 'String',
 'StringValue': 'bank_account_setup' # or 'payment'
 },
 'customer_id': {
 'DataType': 'String',
 'StringValue': 'CUST-001-PREMIUM'
 },
 'message_group_id': {
 'DataType': 'String',
 'StringValue': 'CUST-001-PREMIUM' # Same as customer_id for ordering
 }
 }

def main():
 """Display example message structures"""
 
 print("🧪 FIFO UTILITY CUSTOMER SYSTEM - MESSAGE EXAMPLES")
 print("=" * 60)
 
 print("\nBank Account Setup Message:")
 print(json.dumps(bank_account_setup_message(), indent=2))
 
 print("\n💳 Payment Processing Message:")
 print(json.dumps(payment_message(), indent=2))
 
 print("\nSubscription Control Message:")
 print(json.dumps(subscription_control_message(), indent=2))
 
 print("\n🏷️ SNS Message Attributes (for filtering):")
 print(json.dumps(sns_message_attributes(), indent=2))
 
 print("\nKey Points:")
 print("- transaction_type field determines which SQS queue receives the message")
 print("- customer_id is used as MessageGroupId for FIFO ordering")
 print("- message_group_id field in message body ensures FIFO ordering throughout the flow")
 print("- message_id is used as MessageDeduplicationId for deduplication")
 print("- SNS message attributes enable filtering to appropriate queues")
 print("- Subscription control messages go to separate SNS topic")
 
 print("\nError Testing Customer IDs:")
 print("- CUST-ERROR400-* : Triggers 400 errors (continue processing)")
 print("- CUST-ERROR500-* : Triggers 500 errors (stop subscription)")
 print("- CUST-HAPPY-* : Normal processing (happy path)")

if __name__ == "__main__":
 main()