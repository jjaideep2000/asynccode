#!/usr/bin/env python3
"""
Check Lambda Logs Directly
Look for any errors or issues in Lambda execution
"""

import boto3
import json
from datetime import datetime, timedelta

def check_lambda_logs():
    """Check Lambda logs for any errors or execution issues"""
    
    print("CHECKING LAMBDA LOGS FOR ERRORS")
    print("=" * 50)
    
    logs_client = boto3.client('logs')
    
    # Check last 15 minutes
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)
    
    log_groups = [
        '/aws/lambda/utility-customer-system-dev-bank-account-setup',
        '/aws/lambda/utility-customer-system-dev-payment-processing',
        '/aws/lambda/utility-customer-system-dev-bank-account-observability'
    ]
    
    for log_group in log_groups:
        print(f"\n{log_group.split('/')[-1]}:")
        print("-" * 40)
        
        try:
            # Get ALL recent events (not just filtered ones)
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time_ms,
                endTime=end_time_ms,
                limit=50
            )
            
            if response['events']:
                print(f"Found {len(response['events'])} log events")
                
                # Show recent events
                for event in response['events'][-10:]:  # Last 10 events
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
                    message = event['message'].strip()
                    
                    # Highlight important events
                    if 'ERROR' in message.upper():
                        print(f"   ERROR {timestamp}: {message}")
                    elif 'CUSTOMER_EVENT' in message:
                        print(f"   EVENT {timestamp}: {message}")
                    elif 'CUSTOMER_ERROR' in message:
                        print(f"   ERROR {timestamp}: {message}")
                    elif 'SUBSCRIPTION_DISABLED' in message:
                        print(f"   DISABLED {timestamp}: {message}")
                    elif 'SUBSCRIPTION_ENABLED' in message:
                        print(f"   ENABLED {timestamp}: {message}")
                    elif 'START RequestId' in message:
                        print(f"   START {timestamp}: Lambda execution started")
                    elif 'END RequestId' in message:
                        print(f"   END {timestamp}: Lambda execution completed")
                    elif 'REPORT RequestId' in message:
                        # Extract duration from report
                        if 'Duration:' in message:
                            duration = message.split('Duration: ')[1].split(' ms')[0]
                            print(f"   REPORT {timestamp}: Execution took {duration}ms")
                    else:
                        print(f"   {timestamp}: {message[:100]}...")
                        
            else:
                print(f"No log events found")
                
        except Exception as e:
            print(f"Error checking logs: {e}")

def check_sqs_message_details():
    """Check SQS message details"""
    
    print(f"\nCHECKING SQS MESSAGE DETAILS")
    print("=" * 40)
    
    sqs = boto3.client('sqs')
    
    queue_url = 'https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo'
    
    try:
        # Get queue attributes
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        
        attributes = response['Attributes']
        
        print(f"Bank Account Setup Queue:")
        print(f"   Available Messages: {attributes.get('ApproximateNumberOfMessages', 0)}")
        print(f"   In-Flight Messages: {attributes.get('ApproximateNumberOfMessagesNotVisible', 0)}")
        print(f"   Visibility Timeout: {attributes.get('VisibilityTimeout', 'unknown')} seconds")
        print(f"   Message Retention: {attributes.get('MessageRetentionPeriod', 'unknown')} seconds")
        
        # Try to peek at messages (without removing them)
        try:
            peek_response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=1,
                VisibilityTimeout=1  # Very short visibility timeout
            )
            
            if 'Messages' in peek_response:
                message = peek_response['Messages'][0]
                print(f"\nSample Message in Queue:")
                print(f"   Message ID: {message['MessageId']}")
                print(f"   Receipt Handle: {message['ReceiptHandle'][:20]}...")
                
                # Try to parse the body
                try:
                    body = json.loads(message['Body'])
                    if 'customer_id' in body:
                        print(f"   Customer ID: {body['customer_id']}")
                    if 'Message' in body:
                        # This is an SNS message
                        sns_message = json.loads(body['Message'])
                        if 'customer_id' in sns_message:
                            print(f"   SNS Customer ID: {sns_message['customer_id']}")
                except:
                    print(f"   Body: {message['Body'][:100]}...")
                    
            else:
                print(f"\nNo messages available to peek")
                
        except Exception as e:
            print(f"\nCould not peek at messages: {e}")
            
    except Exception as e:
        print(f"Error checking queue: {e}")

def main():
    """Main function"""
    
    print("LAMBDA LOGS DIRECT CHECKER")
    print("=" * 50)
    print("This will check Lambda logs directly for any execution issues")
    print()
    
    check_lambda_logs()
    check_sqs_message_details()
    
    print(f"\nANALYSIS COMPLETE")
    print("=" * 30)
    print("If you see Lambda execution logs above, the functions are running.")
    print("If you see CUSTOMER_EVENT logs, observability is working.")
    print("If you see errors, that indicates what needs to be fixed.")

if __name__ == "__main__":
    main()