#!/usr/bin/env python3
"""
DEMO 5A: The Crisis Begins - Trigger 500 Errors
Story: "Suddenly, both the bank validation service and payment gateway go down..."
"""

import json
import boto3
import time
from datetime import datetime

# Configuration - SNS Topic ARN
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"

def main():
    """The Crisis Begins - External Services Fail"""
    
    print("DEMO 5A: THE CRISIS BEGINS")
    print("=" * 40)
    print("Story: It's a busy Monday morning at the utility company.")
    print("Customers are setting up bank accounts and making payments.")
    print("Suddenly, disaster strikes - external services start failing!")
    print()
    
    # Use the configured SNS topic ARN
    
    sns_client = boto3.client('sns')
    
    # The first failure - Bank validation service
    print("CRISIS EVENT 1: Bank Validation Service Goes Down")
    print("-" * 50)
    
    bank_customer_id = f"ERROR500-bank-crisis-{int(time.time())}"
    bank_message = {
        'customer_id': bank_customer_id,
        'routing_number': '123456789',
        'account_number': '987654321',
        'account_type': 'checking',
        'bank_name': 'First National Bank',
        'message_id': f"crisis-bank-{int(time.time())}",
        'message_group_id': bank_customer_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print(f"A customer tries to set up their bank account...")
    print(f"Customer: {bank_customer_id}")
    print(f"Bank: {bank_message['bank_name']}")
    print(f"Sending bank account setup request...")
 
    try:
        response = sns_client.publish(
            TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
            Message=json.dumps(bank_message),
            Subject="Bank Account Setup Request (Crisis Scenario)",
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
            MessageDeduplicationId=f"crisis-bank-{bank_customer_id}-{int(time.time())}"
        )
        
        print(f"Request sent via SNS (routed to bank account queue)")
        print(f"SNS Message ID: {response['MessageId']}")
        print(f"Processing... (Bank validation service will fail)")
        
    except Exception as e:
        print(f"Failed to send request: {e}")
        return
 
    time.sleep(2)
    
    # The second failure - Payment gateway
    print(f"\nCRISIS EVENT 2: Payment Gateway Goes Down")
    print("-" * 50)
    
    payment_customer_id = f"ERROR500-payment-crisis-{int(time.time())}"
    payment_message = {
        'customer_id': payment_customer_id,
        'amount': 245.75,
        'payment_method': 'bank_account',
        'currency': 'USD',
        'description': 'Monthly utility bill payment',
        'message_id': f"crisis-payment-{int(time.time())}",
        'message_group_id': payment_customer_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print(f"Another customer tries to pay their utility bill...")
    print(f"Customer: {payment_customer_id}")
    print(f"Amount: ${payment_message['amount']}")
    print(f"Sending payment request...")
    
    try:
        response = sns_client.publish(
            TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
            Message=json.dumps(payment_message),
            Subject="Payment Processing Request (Crisis Scenario)",
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
            MessageDeduplicationId=f"crisis-payment-{payment_customer_id}-{int(time.time())}"
        )
        
        print(f"Request sent via SNS (routed to payment queue)")
        print(f"SNS Message ID: {response['MessageId']}")
        print(f"Processing... (Payment gateway will fail)")
        
    except Exception as e:
        print(f"Failed to send request: {e}")
        return
    
    print(f"\nWaiting for the Lambda functions to process these requests...")
    print(f"(The external services are down - 500 errors incoming!)")
    time.sleep(8)
    
    print(f"\nCHAPTER 1 COMPLETE")
    print(f"The crisis has begun - both external services are failing.")
    print(f"Our Lambda functions are about to encounter 500 errors...")
    print(f"What will happen next? Let's find out!")
    
    print(f"\nNext: Run 'python3 demo_5b_subscriptions_disabled.py'")
    print(f"to see how our intelligent system responds to the crisis!")

if __name__ == "__main__":
    main()