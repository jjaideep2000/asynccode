#!/usr/bin/env python3
"""
Test Centralized Subscription Manager
Verify that the subscription manager can control all Lambda functions
"""

import boto3
import json
import time
from datetime import datetime

def test_subscription_manager():
    """Test the centralized subscription manager functionality"""
    
    print("=== TESTING CENTRALIZED SUBSCRIPTION MANAGER ===")
    
    lambda_client = boto3.client('lambda')
    sns_client = boto3.client('sns')
    
    function_name = "utility-customer-system-dev-subscription-manager"
    topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
    
    # Test 1: Get current status
    print("\n--- Test 1: Get Current Status ---")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({"action": "status"})
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Status retrieval successful")
            
            status_data = json.loads(result['body'])['status']
            
            print(f"Total functions managed: {status_data['summary']['total_functions']}")
            print(f"Enabled functions: {status_data['summary']['enabled_functions']}")
            print(f"Disabled functions: {status_data['summary']['disabled_functions']}")
            
            print("\nFunction Details:")
            for func in status_data['functions']:
                print(f"  {func['service_name']}: {func['overall_status']} "
                      f"({func.get('enabled_mappings', 0)}/{func.get('total_mappings', 0)} enabled)")
        else:
            print(f"❌ Status retrieval failed: {result}")
            
    except Exception as e:
        print(f"❌ Error getting status: {e}")
    
    # Test 2: Direct disable via Lambda invocation
    print("\n--- Test 2: Direct Disable Command ---")
    
    disable_payload = {
        "action": "disable",
        "reason": "Testing centralized subscription management",
        "operator": "test_user"
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(disable_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Disable command successful")
            
            result_data = json.loads(result['body'])['result']
            print(f"Functions processed: {result_data['success_count']} success, {result_data['error_count']} errors")
            
            for func_result in result_data['functions_processed']:
                service_name = func_result['service_name']
                success = func_result['success']
                mappings_disabled = func_result.get('mappings_disabled', 0)
                
                if success:
                    print(f"  ✅ {service_name}: {mappings_disabled} mappings disabled")
                else:
                    print(f"  ❌ {service_name}: {func_result.get('errors', ['Unknown error'])}")
        else:
            print(f"❌ Disable command failed: {result}")
            
    except Exception as e:
        print(f"❌ Error executing disable: {e}")
    
    # Wait a moment for changes to propagate
    print("\nWaiting 5 seconds for changes to propagate...")
    time.sleep(5)
    
    # Test 3: Enable via SNS message
    print("\n--- Test 3: Enable via SNS Message ---")
    
    enable_message = {
        "action": "enable",
        "reason": "Testing SNS-based subscription control",
        "operator": "test_user",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=json.dumps(enable_message),
            Subject="Test: Enable Subscriptions"
        )
        
        print(f"✅ SNS message sent: {response['MessageId']}")
        print("Waiting 10 seconds for SNS processing...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error sending SNS message: {e}")
    
    # Test 4: Verify final status
    print("\n--- Test 4: Verify Final Status ---")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({"action": "status"})
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Final status retrieval successful")
            
            status_data = json.loads(result['body'])['status']
            
            print(f"Final state:")
            print(f"  Enabled functions: {status_data['summary']['enabled_functions']}")
            print(f"  Disabled functions: {status_data['summary']['disabled_functions']}")
            
            print("\nDetailed Status:")
            for func in status_data['functions']:
                print(f"  {func['service_name']}: {func['overall_status']} "
                      f"({func.get('enabled_mappings', 0)}/{func.get('total_mappings', 0)} enabled)")
                
                if func.get('mappings'):
                    for mapping in func['mappings']:
                        queue_name = mapping['event_source_arn'].split(':')[-1]
                        print(f"    - {queue_name}: {mapping['state']}")
        else:
            print(f"❌ Final status retrieval failed: {result}")
            
    except Exception as e:
        print(f"❌ Error getting final status: {e}")

def check_lambda_logs():
    """Check CloudWatch logs for the subscription manager"""
    
    print("\n=== CHECKING SUBSCRIPTION MANAGER LOGS ===")
    
    logs_client = boto3.client('logs')
    log_group_name = "/aws/lambda/utility-customer-system-dev-subscription-manager"
    
    try:
        # Get recent log events
        end_time = int(time.time() * 1000)
        start_time = end_time - (10 * 60 * 1000)  # Last 10 minutes
        
        events = logs_client.filter_log_events(
            logGroupName=log_group_name,
            startTime=start_time,
            endTime=end_time,
            limit=20
        )
        
        print(f"Recent log events (last 10 minutes): {len(events['events'])}")
        
        for event in events['events'][-10:]:  # Show last 10 events
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
            message = event['message'].strip()
            print(f"  {timestamp}: {message}")
            
    except Exception as e:
        print(f"Error checking logs: {e}")

def compare_with_old_system():
    """Compare centralized vs distributed subscription management"""
    
    print("\n=== COMPARISON: CENTRALIZED vs DISTRIBUTED ===")
    
    print("OLD SYSTEM (Distributed):")
    print("  ❌ Each Lambda handles its own subscriptions")
    print("  ❌ Duplicate subscription control logic")
    print("  ❌ Inconsistent behavior across functions")
    print("  ❌ Hard to add new Lambda functions")
    print("  ❌ No centralized monitoring")
    
    print("\nNEW SYSTEM (Centralized):")
    print("  ✅ Single Lambda manages all subscriptions")
    print("  ✅ Centralized subscription control logic")
    print("  ✅ Consistent behavior across all functions")
    print("  ✅ Easy to add new Lambda functions")
    print("  ✅ Centralized monitoring and status")
    print("  ✅ Single point of control via SNS")

if __name__ == "__main__":
    print("Testing Centralized Subscription Manager")
    print("=" * 60)
    
    # Run tests
    test_subscription_manager()
    
    # Check logs
    check_lambda_logs()
    
    # Show comparison
    compare_with_old_system()
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    
    print("\nNext Steps:")
    print("1. Remove subscription control logic from existing Lambdas")
    print("2. Update existing Lambdas to focus only on business logic")
    print("3. Add new Lambda functions to MANAGED_FUNCTIONS config")
    print("4. Monitor centralized subscription management in production")