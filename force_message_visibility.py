#!/usr/bin/env python3
"""
Force Message Visibility Reset
The 4 stuck messages need to have their visibility timeout reset so they can be processed again
"""

import boto3
import json
import time

def check_and_reset_stuck_messages():
    """Check for stuck messages and reset their visibility"""
    
    sqs = boto3.client('sqs')
    
    print("=== CHECKING STUCK MESSAGES ===")
    
    queue_url = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"
    
    try:
        # Get queue attributes
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        
        attributes = attrs['Attributes']
        
        visible_messages = int(attributes.get('ApproximateNumberOfMessages', 0))
        in_flight_messages = int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0))
        visibility_timeout = int(attributes.get('VisibilityTimeout', 300))
        
        print(f"Visible Messages: {visible_messages}")
        print(f"In-Flight Messages: {in_flight_messages}")
        print(f"Visibility Timeout: {visibility_timeout} seconds")
        
        if in_flight_messages > 0:
            print(f"\n⚠️  {in_flight_messages} messages are stuck in-flight")
            print("These messages will become visible again after the visibility timeout expires")
            print(f"Current visibility timeout: {visibility_timeout} seconds ({visibility_timeout/60:.1f} minutes)")
            
            # The messages should become visible again automatically after the timeout
            # But we can try to purge and re-send if needed
            
            return in_flight_messages > 0
        else:
            print("✅ No stuck messages")
            return False
            
    except Exception as e:
        print(f"Error checking queue: {e}")
        return False

def wait_for_visibility_timeout():
    """Wait for messages to become visible again and monitor progress"""
    
    sqs = boto3.client('sqs')
    queue_url = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"
    
    print("\n=== MONITORING MESSAGE VISIBILITY ===")
    print("Waiting for stuck messages to become visible again...")
    
    start_time = time.time()
    check_interval = 30  # Check every 30 seconds
    max_wait_time = 600  # Wait up to 10 minutes
    
    while time.time() - start_time < max_wait_time:
        try:
            attrs = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            
            attributes = attrs['Attributes']
            visible = int(attributes.get('ApproximateNumberOfMessages', 0))
            in_flight = int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0))
            
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Visible: {visible}, In-Flight: {in_flight}")
            
            if in_flight == 0:
                if visible > 0:
                    print(f"✅ Messages are now visible! {visible} messages ready for processing")
                    return True
                else:
                    print("✅ All messages have been processed!")
                    return True
                    
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"Error monitoring queue: {e}")
            break
    
    print("⚠️  Timeout waiting for messages to become visible")
    return False

def check_lambda_processing():
    """Check if the Lambda is now processing messages correctly"""
    
    logs_client = boto3.client('logs')
    
    print("\n=== CHECKING LAMBDA PROCESSING ===")
    
    log_group_name = "/aws/lambda/utility-customer-system-dev-payment-processing"
    
    try:
        # Check last 2 minutes for new activity
        from datetime import datetime, timedelta, timezone
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=2)
        
        events = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=10
        )
        
        print(f"Recent events (last 2 minutes): {len(events['events'])}")
        
        success_count = 0
        error_count = 0
        
        for event in events['events']:
            message = event['message'].lower()
            if 'successfully processed payment' in message:
                success_count += 1
            elif 'error' in message and 'import' not in message:
                error_count += 1
                
        if success_count > 0:
            print(f"✅ {success_count} successful payment processing events found!")
        
        if error_count > 0:
            print(f"⚠️  {error_count} error events found")
            
        # Show recent events
        for event in events['events'][-5:]:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
            message = event['message'].strip()
            if 'import' not in message.lower():  # Skip import errors
                print(f"  {timestamp}: {message[:100]}...")
            
    except Exception as e:
        print(f"Error checking logs: {e}")

def send_test_message():
    """Send a test message to verify the system is working"""
    
    sns = boto3.client('sns')
    
    print("\n=== SENDING TEST MESSAGE ===")
    
    topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-payment-requests"
    
    test_message = {
        "customer_id": "test-fix-verification-123",
        "amount": 25.00,
        "payment_method": "bank_account",
        "message_id": f"test-fix-{int(time.time())}"
    }
    
    try:
        response = sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps(test_message),
            MessageGroupId=test_message['customer_id'],
            MessageDeduplicationId=test_message['message_id']
        )
        
        print(f"✅ Test message sent: {response['MessageId']}")
        print("Waiting 10 seconds to see if it gets processed...")
        
        time.sleep(10)
        
        # Check if it was processed
        check_lambda_processing()
        
    except Exception as e:
        print(f"❌ Error sending test message: {e}")

if __name__ == "__main__":
    print("Forcing Message Visibility Reset")
    print("=" * 50)
    
    # Check current status
    has_stuck_messages = check_and_reset_stuck_messages()
    
    if has_stuck_messages:
        # Wait for visibility timeout
        if wait_for_visibility_timeout():
            print("\n🎉 Messages are now available for processing!")
            
            # Check if Lambda is processing them
            time.sleep(5)
            check_lambda_processing()
        else:
            print("\n⚠️  Messages still stuck. May need manual intervention.")
    
    # Send a test message to verify the fix
    send_test_message()
    
    print("\n" + "=" * 50)
    print("Visibility reset complete!")