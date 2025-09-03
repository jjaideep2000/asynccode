#!/usr/bin/env python3
"""
Test script to verify observability Lambda deployment
Checks that the new Lambda function is working correctly
"""

import boto3
import json
import time

def test_lambda_function():
    """Test the observability Lambda function directly"""
    
    print("Testing Observability Lambda Function")
    print("=" * 40)
    
    lambda_client = boto3.client('lambda')
    function_name = "utility-customer-system-dev-bank-account-observability"
    
    # Test event (simulates SQS record)
    test_event = {
        "Records": [
            {
                "messageId": "test-message-id",
                "receiptHandle": "test-receipt-handle",
                "body": json.dumps({
                    "customer_id": f"TEST-OTEL-{int(time.time())}",
                    "routing_number": "123456789",
                    "account_number": "987654321",
                    "message_id": f"test-{int(time.time())}",
                    "timestamp": "2024-01-01T12:00:00Z"
                }),
                "attributes": {},
                "messageAttributes": {},
                "md5OfBody": "test-md5",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-2:088153174619:utility-customer-system-dev-bank-account-observability.fifo",
                "awsRegion": "us-east-2"
            }
        ]
    }
    
    try:
        print(f"Invoking Lambda function: {function_name}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Read response
        payload = response['Payload'].read()
        result = json.loads(payload)
        
        print(f"Lambda Response:")
        print(f"  Status Code: {response['StatusCode']}")
        print(f"  Result: {result}")
        
        if response['StatusCode'] == 200:
            print("SUCCESS: Lambda function is working!")
            return True
        else:
            print("ERROR: Lambda function returned error")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to invoke Lambda: {e}")
        return False

def check_lambda_logs():
    """Check CloudWatch logs for the test invocation"""
    
    print(f"\nChecking CloudWatch Logs...")
    
    logs_client = boto3.client('logs')
    log_group = '/aws/lambda/utility-customer-system-dev-bank-account-observability'
    
    try:
        # Get recent log events
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=int((time.time() - 300) * 1000),  # Last 5 minutes
            limit=20
        )
        
        if response['events']:
            print(f"Found {len(response['events'])} recent log entries:")
            
            for event in response['events'][-5:]:  # Show last 5 events
                timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
                message = event['message'].strip()
                print(f"  [{timestamp}] {message}")
                
                # Look for observability events
                if 'CUSTOMER_EVENT' in message:
                    print("    ^ Observability event detected!")
                elif 'CUSTOMER_ERROR' in message:
                    print("    ^ Error event detected!")
                elif 'CUSTOMER_METRIC' in message:
                    print("    ^ Metric event detected!")
        else:
            print("No recent log entries found")
            
    except Exception as e:
        print(f"Error checking logs: {e}")

def check_sqs_queue():
    """Check if the observability SQS queue exists"""
    
    print(f"\nChecking SQS Queue...")
    
    sqs = boto3.client('sqs')
    queue_name = "utility-customer-system-dev-bank-account-observability.fifo"
    
    try:
        response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = response['QueueUrl']
        
        print(f"Queue exists: {queue_url}")
        
        # Get queue attributes
        attrs = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        
        print(f"Queue attributes:")
        print(f"  FIFO Queue: {attrs['Attributes'].get('FifoQueue', 'false')}")
        print(f"  Content-Based Deduplication: {attrs['Attributes'].get('ContentBasedDeduplication', 'false')}")
        print(f"  Messages Available: {attrs['Attributes'].get('ApproximateNumberOfMessages', '0')}")
        
        return True
        
    except sqs.exceptions.QueueDoesNotExist:
        print(f"Queue does not exist: {queue_name}")
        return False
    except Exception as e:
        print(f"Error checking queue: {e}")
        return False

def check_event_source_mapping():
    """Check if Lambda has SQS event source mapping"""
    
    print(f"\nChecking Event Source Mapping...")
    
    lambda_client = boto3.client('lambda')
    function_name = "utility-customer-system-dev-bank-account-observability"
    
    try:
        response = lambda_client.list_event_source_mappings(
            FunctionName=function_name
        )
        
        if response['EventSourceMappings']:
            for mapping in response['EventSourceMappings']:
                print(f"Event Source Mapping:")
                print(f"  UUID: {mapping['UUID']}")
                print(f"  State: {mapping['State']}")
                print(f"  Event Source ARN: {mapping['EventSourceArn']}")
                print(f"  Batch Size: {mapping['BatchSize']}")
                
                if 'observability' in mapping['EventSourceArn']:
                    print("  ^ This is the observability queue mapping!")
                    return True
        else:
            print("No event source mappings found")
            return False
            
    except Exception as e:
        print(f"Error checking event source mapping: {e}")
        return False

def main():
    """Main test function"""
    
    print("OBSERVABILITY LAMBDA DEPLOYMENT TEST")
    print("=" * 50)
    
    # Test 1: Check SQS queue
    queue_ok = check_sqs_queue()
    
    # Test 2: Check event source mapping
    mapping_ok = check_event_source_mapping()
    
    # Test 3: Test Lambda function directly
    lambda_ok = test_lambda_function()
    
    # Test 4: Check logs
    check_lambda_logs()
    
    # Summary
    print(f"\nTEST SUMMARY")
    print(f"=" * 20)
    print(f"SQS Queue: {'✓' if queue_ok else '✗'}")
    print(f"Event Source Mapping: {'✓' if mapping_ok else '✗'}")
    print(f"Lambda Function: {'✓' if lambda_ok else '✗'}")
    
    if queue_ok and mapping_ok and lambda_ok:
        print(f"\nSUCCESS: Observability Lambda is ready!")
        print(f"You can now run: python3 demo_observability_bank_account.py")
    else:
        print(f"\nISSUES DETECTED: Some components need attention")
        print(f"Run: python3 deploy_observability_lambda.py")

if __name__ == "__main__":
    main()