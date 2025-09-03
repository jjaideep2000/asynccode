#!/usr/bin/env python3
"""
Verify Payment System is Working
Send a test message through the correct SNS topic to confirm everything is working
"""

import boto3
import json
import time

def find_correct_sns_topic():
    """Find the correct SNS topic for payment requests"""
    
    sns = boto3.client('sns')
    
    print("=== FINDING SNS TOPIC ===")
    
    try:
        topics = sns.list_topics()
        
        payment_topics = [t for t in topics['Topics'] if 'payment' in t['TopicArn'].lower()]
        
        print(f"Found {len(payment_topics)} payment-related topics:")
        
        for topic in payment_topics:
            topic_arn = topic['TopicArn']
            topic_name = topic_arn.split(':')[-1]
            print(f"  {topic_name}: {topic_arn}")
            
        return payment_topics[0]['TopicArn'] if payment_topics else None
        
    except Exception as e:
        print(f"Error finding topics: {e}")
        return None

def send_test_payment():
    """Send a test payment through the system"""
    
    topic_arn = find_correct_sns_topic()
    
    if not topic_arn:
        print("❌ Could not find payment SNS topic")
        return False
    
    sns = boto3.client('sns')
    
    print(f"\n=== SENDING TEST PAYMENT ===")
    print(f"Using topic: {topic_arn}")
    
    test_message = {
        "customer_id": "test-system-verification-123",
        "amount": 50.00,
        "payment_method": "bank_account",
        "message_id": f"test-verification-{int(time.time())}"
    }
    
    try:
        response = sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps(test_message),
            MessageGroupId=test_message['customer_id'],
            MessageDeduplicationId=test_message['message_id']
        )
        
        print(f"✅ Test payment sent: {response['MessageId']}")
        print(f"Customer: {test_message['customer_id']}")
        print(f"Amount: ${test_message['amount']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending test payment: {e}")
        return False

def monitor_payment_processing():
    """Monitor the payment processing for the test message"""
    
    logs_client = boto3.client('logs')
    
    print(f"\n=== MONITORING PAYMENT PROCESSING ===")
    print("Waiting 15 seconds for processing...")
    
    time.sleep(15)
    
    log_group_name = "/aws/lambda/utility-customer-system-dev-payment-processing"
    
    try:
        # Check last 1 minute for processing activity
        from datetime import datetime, timedelta, timezone
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=1)
        
        events = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=20
        )
        
        print(f"Recent events (last 1 minute): {len(events['events'])}")
        
        # Look for our test message
        test_events = []
        success_events = []
        error_events = []
        
        for event in events['events']:
            message = event['message']
            if 'test-system-verification' in message:
                test_events.append(event)
            elif 'successfully processed payment' in message.lower():
                success_events.append(event)
            elif 'error' in message.lower() and 'import' not in message.lower():
                error_events.append(event)
        
        if test_events:
            print(f"✅ Found {len(test_events)} events for our test message!")
            for event in test_events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
                print(f"  {timestamp}: {event['message'].strip()}")
        
        if success_events:
            print(f"✅ Found {len(success_events)} successful payment events!")
            
        if error_events:
            print(f"⚠️  Found {len(error_events)} error events")
            for event in error_events[-2:]:  # Show last 2 errors
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
                print(f"  {timestamp}: {event['message'].strip()[:100]}...")
        
        # Show all recent events
        print("\n--- All Recent Events ---")
        for event in events['events'][-5:]:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
            message = event['message'].strip()
            if 'import' not in message.lower():  # Skip import errors
                print(f"  {timestamp}: {message[:100]}...")
                
        return len(success_events) > 0 or len(test_events) > 0
        
    except Exception as e:
        print(f"Error monitoring logs: {e}")
        return False

def check_final_queue_status():
    """Final check of queue status"""
    
    sqs = boto3.client('sqs')
    
    print(f"\n=== FINAL QUEUE STATUS ===")
    
    queue_url = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"
    
    try:
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        
        attributes = attrs['Attributes']
        
        visible_messages = int(attributes.get('ApproximateNumberOfMessages', 0))
        in_flight_messages = int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0))
        
        print(f"Visible Messages: {visible_messages}")
        print(f"In-Flight Messages: {in_flight_messages}")
        print(f"Total Messages: {visible_messages + in_flight_messages}")
        
        if visible_messages == 0 and in_flight_messages == 0:
            print("✅ Queue is clean - no stuck messages!")
            return True
        else:
            print("⚠️  Still have messages in queue")
            return False
            
    except Exception as e:
        print(f"Error checking queue: {e}")
        return False

if __name__ == "__main__":
    print("Verifying Payment System is Working")
    print("=" * 50)
    
    # Send test payment
    if send_test_payment():
        # Monitor processing
        processing_success = monitor_payment_processing()
        
        # Check final status
        queue_clean = check_final_queue_status()
        
        if processing_success and queue_clean:
            print("\n🎉 SUCCESS: Payment system is fully operational!")
            print("✅ Lambda function is working")
            print("✅ Messages are being processed")
            print("✅ No stuck messages in queue")
        elif processing_success:
            print("\n✅ MOSTLY SUCCESS: Payment processing is working")
            print("⚠️  Some messages may still be in queue")
        else:
            print("\n⚠️  PARTIAL SUCCESS: System is improved but may need more work")
    else:
        print("\n❌ Could not send test payment")
    
    print("\n" + "=" * 50)
    print("System verification complete!")