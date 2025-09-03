#!/usr/bin/env python3
"""
Clear stuck messages from SQS queues
"""

import boto3
import time

def clear_stuck_messages():
    """Clear any stuck messages from SQS queues"""
    
    print("🧹 CLEARING STUCK MESSAGES")
    print("=" * 40)
    
    sqs = boto3.client('sqs')
    
    # Get queue URLs
    try:
        queues_response = sqs.list_queues(QueueNamePrefix='utility-customer-system-dev')
        queue_urls = queues_response.get('QueueUrls', [])
        
        for queue_url in queue_urls:
            queue_name = queue_url.split('/')[-1]
            print(f"\nChecking {queue_name}")
            
            # Get queue attributes
            attrs = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            
            available = int(attrs['Attributes'].get('ApproximateNumberOfMessages', 0))
            in_flight = int(attrs['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
            
            print(f"   Available: {available}, In-Flight: {in_flight}")
            
            if in_flight > 0:
                print(f"   Found {in_flight} in-flight messages")
                print(f"   Waiting for visibility timeout to expire...")
                
                # Wait a bit for visibility timeout
                time.sleep(2)
                
                # Try to receive and delete any visible messages
                while True:
                    response = sqs.receive_message(
                        QueueUrl=queue_url,
                        MaxNumberOfMessages=10,
                        WaitTimeSeconds=1
                    )
                    
                    messages = response.get('Messages', [])
                    if not messages:
                        break
                    
                    for message in messages:
                        print(f"   Deleting message: {message['MessageId'][:8]}...")
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                
                print(f"   Queue cleaned")
            else:
                print(f"   Queue is clean")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_stuck_messages()
    print("\nQueue cleanup complete!")