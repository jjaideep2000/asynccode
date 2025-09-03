#!/usr/bin/env python3
"""
Send test messages to the FIFO utility customer system
"""

import json
import boto3
import random
import uuid
from datetime import datetime

def load_outputs():
 """Load deployment outputs"""
 with open('../deploy/outputs.json', 'r') as f:
 return json.load(f)

def send_transaction_message(sns_client, topic_arn, transaction_type, customer_id, **kwargs):
 """Send transaction message to FIFO SNS topic"""
 
 message_id = f"{transaction_type}-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"
 
 message = {
 "message_id": message_id,
 "transaction_type": transaction_type,
 "customer_id": customer_id,
 "timestamp": datetime.utcnow().isoformat(),
 **kwargs
 }
 
 message_attributes = {
 'transaction_type': {
 'DataType': 'String',
 'StringValue': transaction_type
 }
 }
 
 response = sns_client.publish(
 TopicArn=topic_arn,
 Message=json.dumps(message),
 Subject=f"Transaction: {transaction_type}",
 MessageAttributes=message_attributes,
 MessageGroupId=customer_id,
 MessageDeduplicationId=message_id
 )
 
 print(f"Sent {transaction_type} message for {customer_id}")
 return response['MessageId']

def main():
 outputs = load_outputs()
 sns_client = boto3.client('sns', region_name=outputs['region'])
 
 print("🧪 Sending test messages to FIFO system...")
 
 customers = [
 "CUST-001-PREMIUM",
 "CUST-002-STANDARD", 
 "CUST-ERROR400-TEST",
 "CUST-ERROR500-TEST"
 ]
 
 topic_arn = outputs['transaction_processing_topic_arn']
 
 # Send bank account setup messages
 for customer in customers:
 send_transaction_message(
 sns_client, topic_arn, "bank_account_setup", customer,
 routing_number=f"{random.randint(100000000, 999999999)}",
 account_number=f"{random.randint(1000000000, 9999999999)}",
 account_type="checking"
 )
 
 # Send payment messages
 for customer in customers:
 amount = random.uniform(50, 500)
 send_transaction_message(
 sns_client, topic_arn, "payment", customer,
 amount=round(amount, 2),
 payment_method="bank_account",
 bill_type="utility"
 )
 
 print(f"\nSent {len(customers) * 2} test messages!")
 print("Messages will be routed to appropriate queues based on transaction_type")

if __name__ == "__main__":
 main()
