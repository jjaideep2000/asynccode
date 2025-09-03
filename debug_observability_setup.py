#!/usr/bin/env python3
"""
Debug Observability Setup
Check if observability is properly configured and working
"""

import boto3
import json
import time
from datetime import datetime, timedelta

def check_lambda_functions():
    """Check if Lambda functions exist and their configuration"""
    
    print("CHECKING LAMBDA FUNCTIONS")
    print("=" * 40)
    
    lambda_client = boto3.client('lambda')
    
    functions_to_check = [
        'utility-customer-system-dev-bank-account-setup',
        'utility-customer-system-dev-payment-processing', 
        'utility-customer-system-dev-bank-account-observability'
    ]
    
    for function_name in functions_to_check:
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            print(f"OK {function_name}")
            print(f"   Runtime: {response['Configuration']['Runtime']}")
            print(f"   Last Modified: {response['Configuration']['LastModified']}")
            
            # Check if it has observability code
            try:
                code_response = lambda_client.get_function(FunctionName=function_name)
                # We can't easily check the code content, but we can check environment variables
                env_vars = response['Configuration'].get('Environment', {}).get('Variables', {})
                if env_vars:
                    print(f"   Environment Variables: {list(env_vars.keys())}")
                
            except Exception as e:
                print(f"   Could not check code: {e}")
                
        except Exception as e:
            print(f"ERROR {function_name}: {e}")
        
        print()

def check_recent_lambda_logs():
    """Check recent Lambda logs to see if any observability events are being generated"""
    
    print("CHECKING RECENT LAMBDA LOGS")
    print("=" * 40)
    
    logs_client = boto3.client('logs')
    
    # Check last 30 minutes
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)
    
    log_groups = [
        '/aws/lambda/utility-customer-system-dev-bank-account-setup',
        '/aws/lambda/utility-customer-system-dev-payment-processing',
        '/aws/lambda/utility-customer-system-dev-bank-account-observability'
    ]
    
    for log_group in log_groups:
        print(f"{log_group.split('/')[-1]}:")
        
        try:
            # Check for any recent logs
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time_ms,
                endTime=end_time_ms,
                limit=10
            )
            
            if response['events']:
                print(f"   Found {len(response['events'])} recent log events")
                
                # Check for observability events
                observability_events = 0
                for event in response['events']:
                    if any(keyword in event['message'] for keyword in ['CUSTOMER_EVENT', 'CUSTOMER_ERROR', 'CUSTOMER_METRIC']):
                        observability_events += 1
                
                if observability_events > 0:
                    print(f"   Found {observability_events} observability events")
                else:
                    print(f"   No observability events found")
                    
                # Show sample recent logs
                print(f"   Recent log samples:")
                for event in response['events'][-3:]:
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
                    message = event['message'][:80] + "..." if len(event['message']) > 80 else event['message']
                    print(f"      {timestamp}: {message}")
                    
            else:
                print(f"   No recent log events found")
                
        except Exception as e:
            print(f"   Error checking logs: {e}")
        
        print()

def check_sqs_queues():
    """Check SQS queue status"""
    
    print("CHECKING SQS QUEUES")
    print("=" * 30)
    
    sqs = boto3.client('sqs')
    
    queues = [
        ('Bank Account Setup', 'https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo'),
        ('Payment Processing', 'https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo'),
        ('Observability', 'https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-observability.fifo')
    ]
    
    for queue_name, queue_url in queues:
        try:
            response = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            
            available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
            in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
            
            print(f"{queue_name}:")
            print(f"   Available: {available}")
            print(f"   In-Flight: {in_flight}")
            
        except Exception as e:
            print(f"ERROR {queue_name}: {e}")
        
        print()

def check_lambda_subscriptions():
    """Check Lambda event source mappings"""
    
    print("CHECKING LAMBDA SUBSCRIPTIONS")
    print("=" * 40)
    
    lambda_client = boto3.client('lambda')
    
    functions = [
        'utility-customer-system-dev-bank-account-setup',
        'utility-customer-system-dev-payment-processing',
        'utility-customer-system-dev-bank-account-observability'
    ]
    
    for function_name in functions:
        print(f"{function_name}:")
        
        try:
            response = lambda_client.list_event_source_mappings(FunctionName=function_name)
            
            if response['EventSourceMappings']:
                for mapping in response['EventSourceMappings']:
                    state = mapping['State']
                    source_arn = mapping['EventSourceArn']
                    uuid = mapping['UUID']
                    
                    print(f"   {state} - {source_arn.split(':')[-1]} ({uuid[:8]}...)")
            else:
                print(f"   No event source mappings found")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        print()

def test_observability_function():
    """Test if the observability Lambda function is working"""
    
    print("TESTING OBSERVABILITY FUNCTION")
    print("=" * 40)
    
    lambda_client = boto3.client('lambda')
    
    # Test message
    test_message = {
        'customer_id': f'TEST-{int(time.time())}',
        'routing_number': '123456789',
        'account_number': '987654321',
        'account_type': 'checking',
        'bank_name': 'Test Bank',
        'message_id': f'test-{int(time.time())}',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        print("Invoking observability Lambda function...")
        
        response = lambda_client.invoke(
            FunctionName='utility-customer-system-dev-bank-account-observability',
            Payload=json.dumps(test_message)
        )
        
        if response['StatusCode'] == 200:
            print("Function invoked successfully")
            
            # Check response
            payload = json.loads(response['Payload'].read())
            print(f"Response: {payload}")
            
            # Wait and check logs
            print("Waiting 5 seconds for logs...")
            time.sleep(5)
            
            # Check for observability events in logs
            logs_client = boto3.client('logs')
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=2)
            
            log_response = logs_client.filter_log_events(
                logGroupName='/aws/lambda/utility-customer-system-dev-bank-account-observability',
                startTime=int(start_time.timestamp() * 1000),
                endTime=int(end_time.timestamp() * 1000),
                filterPattern='CUSTOMER_EVENT'
            )
            
            if log_response['events']:
                print(f"Found {len(log_response['events'])} observability events in logs")
                for event in log_response['events'][-2:]:
                    print(f"   {event['message']}")
            else:
                print("No observability events found in logs")
                
        else:
            print(f"Function invocation failed: {response['StatusCode']}")
            
    except Exception as e:
        print(f"Error testing function: {e}")

def main():
    """Main debug function"""
    
    print("OBSERVABILITY DEBUG TOOL")
    print("=" * 50)
    print("This will help diagnose why observability data isn't being captured")
    print()
    
    check_lambda_functions()
    check_recent_lambda_logs()
    check_sqs_queues()
    check_lambda_subscriptions()
    test_observability_function()
    
    print("DIAGNOSIS COMPLETE")
    print("=" * 30)
    print("If you see issues above, the observability system may need to be:")
    print("1. Deployed with the instrumented Lambda code")
    print("2. Configured with proper event source mappings")
    print("3. Set up with the correct SNS subscriptions")
    print()
    print("Run 'python3 complete_observability_setup.py' to fix any issues")

if __name__ == "__main__":
    main()