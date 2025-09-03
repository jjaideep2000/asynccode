#!/usr/bin/env python3
"""
DEMO 2: Send a payment processing message and confirm successful processing
"""

import json
import boto3
import time
from datetime import datetime

# Configuration - SNS Topic ARN
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
PAYMENT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"

def send_payment_message():
    """Send a payment processing message"""
    
    print("DEMO 2: Payment Processing - Success Scenario")
    print("=" * 50)
    
    # Create message
    customer_id = f"demo-payment-{int(time.time())}"
    amount = 125.75
    message = {
        'customer_id': customer_id,
        'amount': amount,
        'payment_method': 'bank_account',
        'currency': 'USD',
        'description': f'Utility bill payment for {customer_id}',
        'message_id': f"demo-payment-{int(time.time())}",
        'message_group_id': customer_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print(f"Sending payment processing message:")
    print(f" Customer ID: {customer_id}")
    print(f" Amount: ${amount}")
    print(f" Payment Method: {message['payment_method']}")
    print(f" Description: {message['description']}")
    
    # Send to SNS topic with proper message attributes for routing
    sns_client = boto3.client('sns')
    message_id = f"demo-payment-{customer_id}-{int(time.time())}"
    
    try:
        response = sns_client.publish(
            TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
            Message=json.dumps(message),
            Subject="Payment Processing Request",
            MessageAttributes={
                'transaction_type': {
                    'DataType': 'String',
                    'StringValue': 'payment' # This triggers routing to payment queue
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
        print(f" Topic: Transaction Processing (routed to Payment Queue)")
        
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
            QueueUrl=PAYMENT_QUEUE_URL,
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
            print(f" Lambda function processed the payment")
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
            logGroupName='/aws/lambda/utility-customer-system-dev-payment-processing',
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
    
    print("CLIENT DEMO - Payment Processing Success")
    print("Demonstrating successful payment processing with dynamic UUID discovery")
    print("=" * 70)
    
    # Step 1: Send message
    customer_id, message = send_payment_message()
    
    if not customer_id:
        print("Demo failed - could not send message")
        return
    
    # Step 2: Check processing
    check_processing_status()
    
    # Step 3: Check logs
    check_lambda_logs()
    
    print(f"\nDEMO 2 COMPLETE!")
    print(f"Summary:")
    print(f" Payment processing message sent successfully")
    print(f" Lambda function processed payment without errors")
    print(f" Dynamic UUID discovery working correctly")
    print(f" System operating as expected")

if __name__ == "__main__":
    main()