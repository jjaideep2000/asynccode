#!/usr/bin/env python3
"""
Extended Payment Logs Check
Look for errors or issues in payment processing over a longer time period
"""

import boto3
import json
from datetime import datetime, timedelta, timezone

def check_extended_logs():
    """Check CloudWatch logs for payment processing over the last hour"""
    
    logs_client = boto3.client('logs')
    
    print("=== EXTENDED PAYMENT PROCESSING LOGS ===")
    
    log_group_name = "/aws/lambda/utility-customer-system-dev-payment-processing"
    
    # Check last hour
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=1)
    
    print(f"Checking logs from {start_time} to {end_time}")
    
    try:
        events = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=50
        )
        
        print(f"Found {len(events['events'])} log events in the last hour")
        
        if events['events']:
            print("\n--- Recent Log Events ---")
            for event in events['events']:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
                message = event['message'].strip()
                print(f"{timestamp}: {message}")
        else:
            print("No log events found in the last hour")
            
        # Check for errors specifically
        error_events = [e for e in events['events'] if any(word in e['message'].lower() for word in ['error', 'exception', 'failed', 'timeout'])]
        
        if error_events:
            print(f"\n--- ERROR EVENTS ({len(error_events)}) ---")
            for event in error_events:
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000, tz=timezone.utc)
                message = event['message'].strip()
                print(f"{timestamp}: {message}")
                
    except Exception as e:
        print(f"Error checking logs: {e}")

def check_lambda_configuration():
    """Check Lambda function configuration for potential issues"""
    
    lambda_client = boto3.client('lambda')
    
    print("\n=== LAMBDA CONFIGURATION CHECK ===")
    
    function_name = "utility-customer-system-dev-payment-processing"
    
    try:
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        
        print(f"Function: {config['FunctionName']}")
        print(f"Timeout: {config['Timeout']} seconds")
        print(f"Memory: {config['MemorySize']} MB")
        print(f"Runtime: {config['Runtime']}")
        print(f"Last Modified: {config['LastModified']}")
        
        # Check if timeout is too short
        if config['Timeout'] < 60:
            print("⚠️  WARNING: Function timeout might be too short for payment processing")
            
        # Check reserved concurrency
        try:
            concurrency = lambda_client.get_provisioned_concurrency_config(FunctionName=function_name)
            print(f"Provisioned Concurrency: {concurrency.get('ProvisionedConcurrencyConfig', {}).get('ProvisionedConcurrency', 'None')}")
        except:
            print("Provisioned Concurrency: None")
            
        try:
            reserved = lambda_client.get_function_concurrency(FunctionName=function_name)
            print(f"Reserved Concurrency: {reserved.get('ReservedConcurrencyExecutions', 'None')}")
        except:
            print("Reserved Concurrency: None")
            
    except Exception as e:
        print(f"Error checking Lambda configuration: {e}")

def check_sqs_dlq():
    """Check the dead letter queue for failed messages"""
    
    sqs = boto3.client('sqs')
    
    print("\n=== DEAD LETTER QUEUE CHECK ===")
    
    dlq_name = "utility-customer-system-dev-payment-processing-dlq.fifo"
    
    try:
        # Get DLQ URL
        queues = sqs.list_queues()
        dlq_url = None
        
        for queue_url in queues.get('QueueUrls', []):
            if dlq_name in queue_url:
                dlq_url = queue_url
                break
                
        if dlq_url:
            print(f"DLQ URL: {dlq_url}")
            
            # Check DLQ attributes
            attrs = sqs.get_queue_attributes(
                QueueUrl=dlq_url,
                AttributeNames=['All']
            )
            
            attributes = attrs['Attributes']
            dlq_messages = int(attributes.get('ApproximateNumberOfMessages', 0))
            
            print(f"Messages in DLQ: {dlq_messages}")
            
            if dlq_messages > 0:
                print(f"⚠️  WARNING: {dlq_messages} messages in dead letter queue!")
                
                # Try to peek at DLQ messages
                try:
                    response = sqs.receive_message(
                        QueueUrl=dlq_url,
                        MaxNumberOfMessages=1,
                        WaitTimeSeconds=1,
                        VisibilityTimeout=1
                    )
                    
                    if 'Messages' in response:
                        message = response['Messages'][0]
                        body = json.loads(message['Body'])
                        
                        print("\n--- Sample DLQ Message ---")
                        if 'Message' in body:
                            inner_message = json.loads(body['Message'])
                            print(f"Customer ID: {inner_message.get('customer_id', 'N/A')}")
                            print(f"Amount: ${inner_message.get('amount', 'N/A')}")
                        else:
                            print(f"Customer ID: {body.get('customer_id', 'N/A')}")
                            print(f"Amount: ${body.get('amount', 'N/A')}")
                            
                        print(f"Message ID: {message['MessageId']}")
                        
                except Exception as e:
                    print(f"Could not peek at DLQ message: {e}")
            else:
                print("✅ No messages in dead letter queue")
        else:
            print("Dead letter queue not found")
            
    except Exception as e:
        print(f"Error checking DLQ: {e}")

def test_lambda_directly():
    """Test the Lambda function directly to see if it's working"""
    
    lambda_client = boto3.client('lambda')
    
    print("\n=== DIRECT LAMBDA TEST ===")
    
    function_name = "utility-customer-system-dev-payment-processing"
    
    test_payload = {
        "customer_id": "test-customer-123",
        "amount": 100.00,
        "payment_method": "bank_account",
        "message_id": "test-message-123"
    }
    
    try:
        print("Testing Lambda function with sample payload...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"Status Code: {status_code}")
        print(f"Response: {json.dumps(payload, indent=2)}")
        
        if status_code == 200:
            print("✅ Lambda function is working correctly")
        else:
            print("❌ Lambda function returned an error")
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")

if __name__ == "__main__":
    print("Extended Payment Processing Investigation")
    print("=" * 60)
    
    check_extended_logs()
    check_lambda_configuration()
    check_sqs_dlq()
    test_lambda_directly()
    
    print("\n" + "=" * 60)
    print("Extended investigation complete!")