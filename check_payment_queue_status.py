#!/usr/bin/env python3
"""
Check Payment Queue Status
Investigates why messages might be stuck in the payment processing queue
"""

import boto3
import json
from datetime import datetime, timedelta

def check_queue_status():
    """Check the status of payment processing queues"""
    
    sqs = boto3.client('sqs')
    
    # Get all queues
    try:
        queues = sqs.list_queues()
        payment_queues = [q for q in queues.get('QueueUrls', []) if 'payment' in q.lower()]
        
        print("=== PAYMENT QUEUE STATUS ===")
        print(f"Found {len(payment_queues)} payment-related queues:")
        
        for queue_url in payment_queues:
            queue_name = queue_url.split('/')[-1]
            print(f"\n--- Queue: {queue_name} ---")
            print(f"URL: {queue_url}")
            
            # Get queue attributes
            try:
                attrs = sqs.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['All']
                )
                
                attributes = attrs['Attributes']
                
                # Key metrics
                visible_messages = int(attributes.get('ApproximateNumberOfMessages', 0))
                in_flight_messages = int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0))
                delayed_messages = int(attributes.get('ApproximateNumberOfMessagesDelayed', 0))
                
                print(f"Visible Messages: {visible_messages}")
                print(f"In-Flight Messages: {in_flight_messages}")
                print(f"Delayed Messages: {delayed_messages}")
                print(f"Total Messages: {visible_messages + in_flight_messages + delayed_messages}")
                
                # Queue configuration
                visibility_timeout = int(attributes.get('VisibilityTimeout', 0))
                message_retention = int(attributes.get('MessageRetentionPeriod', 0))
                max_receive_count = attributes.get('RedrivePolicy')
                
                print(f"Visibility Timeout: {visibility_timeout} seconds")
                print(f"Message Retention: {message_retention // 3600} hours")
                
                if max_receive_count:
                    redrive_policy = json.loads(max_receive_count)
                    print(f"Max Receive Count: {redrive_policy.get('maxReceiveCount', 'N/A')}")
                    print(f"Dead Letter Queue: {redrive_policy.get('deadLetterTargetArn', 'None')}")
                
                # Check for stuck messages
                if visible_messages > 0:
                    print(f"\n⚠️  WARNING: {visible_messages} messages waiting to be processed!")
                    
                if in_flight_messages > 0:
                    print(f"⚠️  WARNING: {in_flight_messages} messages currently being processed (or stuck)")
                    
                # Try to peek at a message without consuming it
                if visible_messages > 0:
                    print("\n--- Sample Message (peek) ---")
                    try:
                        response = sqs.receive_message(
                            QueueUrl=queue_url,
                            MaxNumberOfMessages=1,
                            WaitTimeSeconds=1,
                            VisibilityTimeout=1  # Very short timeout so message becomes visible again quickly
                        )
                        
                        if 'Messages' in response:
                            message = response['Messages'][0]
                            body = json.loads(message['Body'])
                            
                            # If it's an SNS message, extract the inner message
                            if 'Message' in body:
                                inner_message = json.loads(body['Message'])
                                print(f"Customer ID: {inner_message.get('customer_id', 'N/A')}")
                                print(f"Amount: ${inner_message.get('amount', 'N/A')}")
                                print(f"Payment Method: {inner_message.get('payment_method', 'N/A')}")
                            else:
                                print(f"Customer ID: {body.get('customer_id', 'N/A')}")
                                print(f"Amount: ${body.get('amount', 'N/A')}")
                                print(f"Payment Method: {body.get('payment_method', 'N/A')}")
                            
                            print(f"Message ID: {message['MessageId']}")
                            print(f"Receive Count: {message.get('Attributes', {}).get('ApproximateReceiveCount', 'N/A')}")
                            
                    except Exception as e:
                        print(f"Could not peek at message: {e}")
                
            except Exception as e:
                print(f"Error getting queue attributes: {e}")
                
    except Exception as e:
        print(f"Error listing queues: {e}")

def check_lambda_function_status():
    """Check if the payment processing Lambda is working correctly"""
    
    lambda_client = boto3.client('lambda')
    
    print("\n=== LAMBDA FUNCTION STATUS ===")
    
    try:
        # List functions with 'payment' in the name
        functions = lambda_client.list_functions()
        payment_functions = [f for f in functions['Functions'] if 'payment' in f['FunctionName'].lower()]
        
        for func in payment_functions:
            func_name = func['FunctionName']
            print(f"\n--- Function: {func_name} ---")
            print(f"Runtime: {func['Runtime']}")
            print(f"Last Modified: {func['LastModified']}")
            print(f"State: {func.get('State', 'N/A')}")
            print(f"State Reason: {func.get('StateReason', 'N/A')}")
            
            # Check event source mappings (SQS triggers)
            try:
                mappings = lambda_client.list_event_source_mappings(FunctionName=func_name)
                
                print(f"Event Source Mappings: {len(mappings['EventSourceMappings'])}")
                
                for mapping in mappings['EventSourceMappings']:
                    print(f"  - Source: {mapping.get('EventSourceArn', 'N/A')}")
                    print(f"    State: {mapping.get('State', 'N/A')}")
                    print(f"    Batch Size: {mapping.get('BatchSize', 'N/A')}")
                    print(f"    Last Modified: {mapping.get('LastModified', 'N/A')}")
                    
                    if mapping.get('State') != 'Enabled':
                        print(f"    ⚠️  WARNING: Event source mapping is not enabled!")
                        
            except Exception as e:
                print(f"Error checking event source mappings: {e}")
                
    except Exception as e:
        print(f"Error checking Lambda functions: {e}")

def check_cloudwatch_logs():
    """Check recent CloudWatch logs for payment processing"""
    
    logs_client = boto3.client('logs')
    
    print("\n=== RECENT CLOUDWATCH LOGS ===")
    
    try:
        # Find log groups for payment processing
        log_groups = logs_client.describe_log_groups()
        payment_log_groups = [lg for lg in log_groups['logGroups'] if 'payment' in lg['logGroupName'].lower()]
        
        for log_group in payment_log_groups:
            log_group_name = log_group['logGroupName']
            print(f"\n--- Log Group: {log_group_name} ---")
            
            # Get recent log events (last 10 minutes)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=10)
            
            try:
                events = logs_client.filter_log_events(
                    logGroupName=log_group_name,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000),
                    limit=10
                )
                
                print(f"Recent events (last 10 minutes): {len(events['events'])}")
                
                for event in events['events'][-5:]:  # Show last 5 events
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                    print(f"  {timestamp}: {event['message'][:100]}...")
                    
                if not events['events']:
                    print("  No recent log events found")
                    
            except Exception as e:
                print(f"Error reading log events: {e}")
                
    except Exception as e:
        print(f"Error checking CloudWatch logs: {e}")

if __name__ == "__main__":
    print("Checking Payment Queue Status...")
    print("=" * 50)
    
    check_queue_status()
    check_lambda_function_status()
    check_cloudwatch_logs()
    
    print("\n" + "=" * 50)
    print("Investigation complete!")