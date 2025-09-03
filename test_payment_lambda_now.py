#!/usr/bin/env python3
"""
Test Payment Lambda After Redeployment
"""

import boto3
import json
import time

def test_lambda_function():
    """Test the Lambda function to see if it's working now"""
    
    lambda_client = boto3.client('lambda')
    function_name = "utility-customer-system-dev-payment-processing"
    
    print("=== TESTING PAYMENT LAMBDA ===")
    
    test_payload = {
        "customer_id": "test-customer-working-123",
        "amount": 100.00,
        "payment_method": "bank_account",
        "message_id": "test-working-message-123"
    }
    
    try:
        print("Testing Lambda function...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"Status Code: {status_code}")
        print(f"Response: {json.dumps(payload, indent=2)}")
        
        if status_code == 200 and 'errorMessage' not in payload:
            print("✅ Lambda function is working correctly!")
            return True
        else:
            print("❌ Lambda function still has issues")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")
        return False

def check_queue_status_again():
    """Check if the stuck messages are being processed"""
    
    sqs = boto3.client('sqs')
    
    print("\n=== CHECKING QUEUE STATUS ===")
    
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
        
        if in_flight_messages == 0 and visible_messages == 0:
            print("✅ All messages have been processed!")
        elif in_flight_messages < 4:
            print(f"✅ Progress! Messages being processed (was 4, now {in_flight_messages})")
        else:
            print("⚠️  Messages still stuck")
            
    except Exception as e:
        print(f"Error checking queue: {e}")

def check_recent_logs():
    """Check for recent log activity"""
    
    logs_client = boto3.client('logs')
    
    print("\n=== CHECKING RECENT LOGS ===")
    
    log_group_name = "/aws/lambda/utility-customer-system-dev-payment-processing"
    
    try:
        # Check last 5 minutes
        from datetime import datetime, timedelta, timezone
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=5)
        
        events = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=20
        )
        
        print(f"Recent events (last 5 minutes): {len(events['events'])}")
        
        for event in events['events']:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
            message = event['message'].strip()
            print(f"  {timestamp}: {message}")
            
        if not events['events']:
            print("  No recent activity")
            
    except Exception as e:
        print(f"Error checking logs: {e}")

if __name__ == "__main__":
    print("Testing Payment Lambda After Redeployment")
    print("=" * 50)
    
    # Test the function
    if test_lambda_function():
        print("\n🎉 Lambda is working! Checking if stuck messages are being processed...")
        
        # Wait a moment for processing
        time.sleep(5)
        
        # Check queue status
        check_queue_status_again()
        
        # Check logs
        check_recent_logs()
    else:
        print("\n❌ Lambda still not working. Need to investigate further.")
    
    print("\n" + "=" * 50)
    print("Test complete!")