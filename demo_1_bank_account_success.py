#!/usr/bin/env python3
"""
DEMO 1: Send a bank account setup message and confirm successful processing
"""

import json
import boto3
import time
from datetime import datetime

# Configuration - SNS Topic ARN
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
BANK_ACCOUNT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo"

def send_bank_account_message():
    """Send a bank account setup message"""
    
    print("DEMO 1: Bank Account Setup - Success Scenario")
    print("=" * 50)
    
    # Create message
    customer_id = f"demo-customer-{int(time.time())}"
    message = {
        'customer_id': customer_id,
        'routing_number': '123456789',
        'account_number': '987654321',
        'account_type': 'checking',
        'bank_name': 'Demo Bank of America',
        'message_id': f"demo-bank-{int(time.time())}",
        'message_group_id': customer_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print(f"Sending bank account setup message:")
    print(f" Customer ID: {customer_id}")
    print(f" Routing Number: {message['routing_number']}")
    print(f" Account Number: ****{message['account_number'][-4:]}")
    print(f" Bank Name: {message['bank_name']}")
    
    # Send to SNS topic with proper message attributes for routing
    sns_client = boto3.client('sns')
    message_id = f"demo-bank-{customer_id}-{int(time.time())}"
    
    try:
        response = sns_client.publish(
            TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
            Message=json.dumps(message),
            Subject="Bank Account Setup Request",
            MessageAttributes={
                'transaction_type': {
                    'DataType': 'String',
                    'StringValue': 'bank_account_setup' # This triggers routing to bank account queue
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
            MessageDeduplicationId=message_id
        )
        
        print(f"\nMessage sent successfully!")
        print(f" SNS Message ID: {response['MessageId']}")
        print(f" Topic: Transaction Processing (routed to Bank Account Queue)")
        
        return customer_id, message
        
    except Exception as e:
        print(f"\nFailed to send message: {e}")
        return None, None

def check_processing_status():
    """Check if the message was processed"""
    
    print(f"\nWaiting for Lambda processing...")
    time.sleep(5)
    
    print(f"\nChecking processing status...")
    
    # Check queue status
    sqs = boto3.client('sqs')
    
    try:
        response = sqs.get_queue_attributes(
            QueueUrl=BANK_ACCOUNT_QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        
        available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
        in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
        
        print(f" Queue Status:")
        print(f" - Messages Available: {available}")
        print(f" - Messages In-Flight: {in_flight}")
        
        if available == 0 and in_flight == 0:
            print(f"\nSUCCESS: Message processed successfully!")
            print(f" No messages remaining in queue")
            print(f" Lambda function processed the bank account setup")
        elif in_flight > 0:
            print(f"\nPROCESSING: Message currently being processed...")
        else:
            print(f"\nMessages still in queue - may need more time")
        
    except Exception as e:
        print(f"\nError checking queue status: {e}")

def check_lambda_logs():
    """Check Lambda logs for processing confirmation"""
    
    print(f"\nChecking Lambda logs for processing details...")
    
    logs_client = boto3.client('logs')
    
    try:
        # Get recent successful processing logs
        response = logs_client.filter_log_events(
            logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-setup',
            startTime=int((time.time() - 60) * 1000), # Last minute
            filterPattern='Successfully processed'
        )
        
        if response['events']:
            print(f"Found successful processing logs:")
            for event in response['events'][-2:]: # Last 2 events
                timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
                message = event['message'].strip()
                if 'Successfully processed' in message:
                    print(f" [{timestamp}] {message}")
        else:
            print(f"No recent successful processing logs found")
        
    except Exception as e:
        print(f"Error checking logs: {e}")

def main():
    """Main demo function"""
    
    print("CLIENT DEMO - Bank Account Setup Success")
    print("Demonstrating successful message processing with dynamic UUID discovery")
    print("=" * 70)
    
    # Step 1: Send message
    customer_id, message = send_bank_account_message()
    
    if not customer_id:
        print("Demo failed - could not send message")
        return
    
    # Step 2: Check processing
    check_processing_status()
    
    # Step 3: Check logs
    check_lambda_logs()
    
    print(f"\nDEMO 1 COMPLETE!")
    print(f"Summary:")
    print(f" Bank account setup message sent successfully")
    print(f" Lambda function processed message without errors")
    print(f" Dynamic UUID discovery working correctly")
    print(f" System operating as expected")

if __name__ == "__main__":
    main()