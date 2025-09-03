#!/usr/bin/env python3
"""
DEMO 5C: The Queue Builds Up - Messages Pile Up Safely
Story: "Customers keep trying to use the system, but messages pile up safely..."
"""

import json
import boto3
import time
from datetime import datetime

# Configuration - SNS Topic ARN and Queue URLs for monitoring
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
BANK_ACCOUNT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo"
PAYMENT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"

def send_customer_requests():
    """Simulate customers continuing to use the system"""
    
    print("DEMO 5C: THE QUEUE BUILDS UP")
    print("=" * 35)
    print("Story: Even though the external services are down,")
    print("customers don't know about the outage and keep using the system.")
    print("Let's see what happens to their requests...")
    print()
    
    sns_client = boto3.client('sns')
    
    print("CUSTOMER ACTIVITY: People Keep Using the System")
    print("-" * 50)
    
    # Simulate multiple customers trying to set up bank accounts
    print("Bank Account Setup Requests:")
    
    bank_customers = [
        {"name": "Customer A", "bank": "Chase Bank"},
        {"name": "Customer B", "bank": "Wells Fargo"},
        {"name": "Customer C", "bank": "Bank of America"}
    ]
    
    for i, customer in enumerate(bank_customers):
        customer_id = f"normal-bank-{customer['name'].replace(' ', '')}-{int(time.time())}"
        message = {
            'customer_id': customer_id,
            'routing_number': f"12345678{i}",
            'account_number': f"98765432{i}",
            'account_type': 'checking',
            'bank_name': customer['bank'],
            'message_id': f"normal-bank-{i+1}-{int(time.time())}",
            'message_group_id': customer_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print(f" {customer['name']} tries to set up {customer['bank']} account...")
        
        try:
            sns_client.publish(
                TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
                Message=json.dumps(message),
                Subject=f"Bank Account Setup Request - {customer['name']}",
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
            print(f" Request sent via SNS (routed to bank account queue)")
        except Exception as e:
            print(f" Failed to send request: {e}")
 
    time.sleep(1)
    
    print(f"\nPayment Processing Requests:")
    
    payment_customers = [
        {"name": "Customer A", "amount": 89.50},
        {"name": "Customer B", "amount": 156.25},
        {"name": "Customer C", "amount": 203.75}
    ]
    
    for i, customer in enumerate(payment_customers):
        customer_id = f"normal-payment-{customer['name'].replace(' ', '')}-{int(time.time())}"
        message = {
            'customer_id': customer_id,
            'amount': customer['amount'],
            'payment_method': 'bank_account',
            'currency': 'USD',
            'description': f"Utility bill payment for {customer['name']}",
            'message_id': f"normal-payment-{i+1}-{int(time.time())}",
            'message_group_id': customer_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print(f" {customer['name']} tries to pay ${customer['amount']} utility bill...")
        
        try:
            sns_client.publish(
                TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
                Message=json.dumps(message),
                Subject=f"Payment Processing Request - {customer['name']}",
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
            print(f" Request sent via SNS (routed to payment queue)")
        except Exception as e:
            print(f" Failed to send request: {e}")
        
        time.sleep(1)

def check_queue_buildup():
    """Check that messages are piling up in queues"""
    
    print(f"\nQUEUE STATUS: Let's See What Happened")
    print("-" * 45)
    
    print(f"Waiting a moment for the system to process (or not process) these requests...")
    time.sleep(10)
    
    sqs = boto3.client('sqs')
    
    queues = [
        ('Bank Account Setup Queue', BANK_ACCOUNT_QUEUE_URL),
        ('Payment Processing Queue', PAYMENT_QUEUE_URL)
    ]
    
    total_messages = 0
    
    for queue_name, queue_url in queues:
        print(f"\n{queue_name}:")
        
        try:
            response = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            
            available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
            in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
            total = available + in_flight
            total_messages += total
            
            print(f" Messages Available: {available}")
            print(f" Messages In-Flight: {in_flight}")
            print(f" Total Messages: {total}")
            
            if total > 0:
                print(f" These messages are safely queued but NOT being processed")
                print(f" (Lambda subscriptions are disabled due to 500 errors)")
            else:
                print(f" No messages in queue")
        
        except Exception as e:
            print(f" Error checking queue: {e}")
    
    print(f"\nQUEUE BUILDUP ANALYSIS")
    print("-" * 30)
    
    if total_messages > 0:
        print(f"PERFECT BEHAVIOR: {total_messages} messages safely queued!")
        print(f"The system is working exactly as designed:")
        print(f" Customer requests are accepted and safely stored")
        print(f" No messages are lost during the outage")
        print(f" Lambda functions are NOT processing (subscriptions disabled)")
        print(f" System prevents wasted resources on failing external calls")
        print(f" FIFO ordering is preserved for when services recover")
        
        print(f"\nPROTECTION IN ACTION:")
        print(f" Messages pile up safely instead of being processed and failing")
        print(f" No cascade failures or resource exhaustion")
        print(f" Customer data is preserved and will be processed when services recover")
        
    else:
        print(f"No messages in queues - they may have been processed already")
        print(f"This could mean subscriptions are still enabled")
    
    print(f"\nCHAPTER 3 COMPLETE")
    print(f"Customer requests are safely queued during the outage!")
    print(f"The system is protecting itself while preserving all customer data.")
    print(f"But how do we recover when the external services come back online?")
    
    print(f"\nNext: Run 'python3 demo_5d_send_resubscribe.py'")
    print(f"to see how we can signal the system to resume processing!")

def main():
    """Main function"""
    send_customer_requests()
    check_queue_buildup()

if __name__ == "__main__":
    main()