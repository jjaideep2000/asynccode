#!/usr/bin/env python3
"""
Demo: 500 Error Handling with Observability
Shows how 500 errors are detected, logged, and handled with subscription control
"""

import json
import boto3
import time
from datetime import datetime
from observability.otel_config import get_bank_account_observability

# Configuration
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
SUBSCRIPTION_CONTROL_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"

def send_500_error_message():
    """Send a message that will trigger a 500 error"""
    
    print("500 ERROR OBSERVABILITY DEMO")
    print("Demonstrating 500 error detection and subscription control")
    print("=" * 60)
    
    # Initialize observability
    observability = get_bank_account_observability()
    
    # Generate customer data with ERROR500 trigger
    customer_id = f"ERROR500-OTEL-{int(time.time())}"
    
    # Start customer journey trace
    trace_info = observability.start_customer_trace(
        operation="500_error_demo",
        customer_id=customer_id,
        message_attributes={
            "demo_type": "500_error_handling",
            "expected_outcome": "subscription_disabled"
        }
    )
    
    print(f"Started 500 Error Demo Trace:")
    print(f"  Customer ID: {customer_id}")
    print(f"  Trace ID: {trace_info['trace_id']}")
    print(f"  Expected: 500 error -> subscription disabled")
    
    # Create message that will trigger 500 error
    message = {
        'customer_id': customer_id,
        'routing_number': '123456789',
        'account_number': '987654321500',  # Will trigger 500 error
        'message_id': f"500-error-demo-{int(time.time())}",
        'message_group_id': customer_id,
        'timestamp': datetime.utcnow().isoformat(),
        'demo_500_error': True
    }
    
    # Send to SNS
    try:
        sns_client = boto3.client('sns')
        response = sns_client.publish(
            TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
            Message=json.dumps(message),
            Subject="500 Error Demo - Bank Account Setup",
            MessageAttributes={
                'transaction_type': {
                    'DataType': 'String',
                    'StringValue': 'bank_account_setup'
                },
                'customer_id': {
                    'DataType': 'String',
                    'StringValue': customer_id
                },
                'message_group_id': {
                    'DataType': 'String',
                    'StringValue': customer_id
                },
                'observability_demo': {
                    'DataType': 'String',
                    'StringValue': 'true'
                }
            },
            MessageGroupId=customer_id,
            MessageDeduplicationId=f"500-error-{customer_id}-{int(time.time())}"
        )
        
        observability.record_customer_event(
            event_type="500_error_message_sent",
            customer_id=customer_id,
            status="success",
            details={
                "sns_message_id": response['MessageId'],
                "expected_error": "bank_validation_service_unavailable"
            }
        )
        
        print(f"\n500 Error Message Sent:")
        print(f"  SNS Message ID: {response['MessageId']}")
        print(f"  Customer ID contains 'ERROR500' - will trigger 500 error")
        
        return customer_id, response['MessageId']
        
    except Exception as e:
        observability.record_error(
            error_type="demo_setup_error",
            customer_id=customer_id,
            error_message=str(e)
        )
        print(f"Failed to send 500 error message: {e}")
        return None, None

def monitor_500_error_handling(customer_id: str):
    """Monitor the 500 error handling process"""
    
    print(f"\nMonitoring 500 Error Handling:")
    print(f"  Customer ID: {customer_id}")
    print("-" * 40)
    
    observability = get_bank_account_observability()
    
    # Monitor for 30 seconds
    for check in range(6):  # 6 checks, 5 seconds apart
        print(f"\nCheck {check + 1}/6 (after {check * 5} seconds):")
        
        # Check Lambda logs for 500 error events
        check_error_logs(customer_id)
        
        # Check subscription status
        check_subscription_status()
        
        if check < 5:  # Don't sleep on last iteration
            time.sleep(5)
    
    observability.record_customer_event(
        event_type="500_error_monitoring_completed",
        customer_id=customer_id,
        status="success",
        details={
            "monitoring_duration_seconds": 30,
            "checks_performed": 6
        }
    )

def check_error_logs(customer_id: str):
    """Check CloudWatch logs for 500 error events"""
    
    try:
        logs_client = boto3.client('logs')
        log_group = '/aws/lambda/utility-customer-system-dev-bank-account-observability'
        
        # Search for customer-specific error logs
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            filterPattern=f'"{customer_id}"',
            startTime=int((time.time() - 300) * 1000),  # Last 5 minutes
            limit=10
        )
        
        error_events_found = []
        
        if response['events']:
            for event in response['events']:
                message = event['message']
                
                if 'CUSTOMER_ERROR' in message and customer_id in message:
                    error_events_found.append("Error event detected")
                elif '500_error_detected' in message:
                    error_events_found.append("500 error detection logged")
                elif 'subscription_disabled' in message:
                    error_events_found.append("Subscription disabled")
                elif 'SUBSCRIPTION_DISABLED' in message:
                    error_events_found.append("Subscription control executed")
        
        if error_events_found:
            print(f"  Error Handling Events: {len(error_events_found)} found")
            for event in error_events_found:
                print(f"    - {event}")
        else:
            print(f"  Error Handling Events: No events found yet")
            
    except Exception as e:
        print(f"  Error checking logs: {e}")

def check_subscription_status():
    """Check the current subscription status"""
    
    try:
        lambda_client = boto3.client('lambda')
        function_name = "utility-customer-system-dev-bank-account-observability"
        
        response = lambda_client.list_event_source_mappings(FunctionName=function_name)
        
        if response['EventSourceMappings']:
            for mapping in response['EventSourceMappings']:
                if 'observability' in mapping['EventSourceArn']:
                    state = mapping['State']
                    print(f"  Subscription Status: {state}")
                    
                    if state == 'Disabled':
                        print(f"    SUCCESS: Subscription disabled due to 500 error!")
                    elif state == 'Enabled':
                        print(f"    Subscription still enabled (500 error may not have occurred yet)")
                    
                    return state
        
        print(f"  Subscription Status: No mappings found")
        return None
        
    except Exception as e:
        print(f"  Error checking subscription: {e}")
        return None

def send_resubscribe_message():
    """Send a resubscribe message to re-enable processing"""
    
    print(f"\nSending Resubscribe Message...")
    
    observability = get_bank_account_observability()
    
    try:
        sns_client = boto3.client('sns')
        
        control_message = {
            'action': 'enable',
            'timestamp': datetime.utcnow().isoformat(),
            'source': '500_error_demo_recovery'
        }
        
        response = sns_client.publish(
            TopicArn=SUBSCRIPTION_CONTROL_TOPIC_ARN,
            Message=json.dumps(control_message),
            Subject='Demo: Re-enable Subscriptions After 500 Error'
        )
        
        observability.record_customer_event(
            event_type="resubscribe_message_sent",
            customer_id="system",
            status="success",
            details={
                "sns_message_id": response['MessageId'],
                "action": "enable",
                "reason": "500_error_demo_recovery"
            }
        )
        
        print(f"  Resubscribe message sent: {response['MessageId']}")
        print(f"  This should re-enable the subscription")
        
        return True
        
    except Exception as e:
        observability.record_error(
            error_type="resubscribe_error",
            customer_id="system",
            error_message=str(e)
        )
        print(f"  Failed to send resubscribe message: {e}")
        return False

def show_500_error_summary(customer_id: str):
    """Show summary of 500 error handling"""
    
    print(f"\n500 ERROR HANDLING SUMMARY")
    print("=" * 40)
    print(f"Customer ID: {customer_id}")
    print(f"Demo Type: 500 Error with Subscription Control")
    print(f"\nObservability Features Demonstrated:")
    print(f"  - 500 error detection and classification")
    print(f"  - Automatic subscription disabling")
    print(f"  - Error event logging and tracking")
    print(f"  - Subscription control via SNS messages")
    print(f"  - Complete error recovery workflow")
    
    print(f"\nFor Customer Support:")
    print(f"  1. Search CloudWatch logs for: {customer_id}")
    print(f"  2. Look for events: 500_error_detected, subscription_disabled")
    print(f"  3. Track error recovery: resubscribe_message_sent")
    print(f"  4. Monitor subscription status changes")

def main():
    """Main demo function"""
    
    # Step 1: Send 500 error message
    customer_id, sns_message_id = send_500_error_message()
    
    if not customer_id:
        print("Demo failed - could not send 500 error message")
        return
    
    # Step 2: Monitor 500 error handling
    monitor_500_error_handling(customer_id)
    
    # Step 3: Send resubscribe message
    resubscribe_sent = send_resubscribe_message()
    
    if resubscribe_sent:
        print(f"\nWaiting 10 seconds for resubscription...")
        time.sleep(10)
        
        # Check final subscription status
        final_status = check_subscription_status()
        if final_status == 'Enabled':
            print(f"SUCCESS: Subscription re-enabled!")
        else:
            print(f"Subscription status: {final_status}")
    
    # Step 4: Show summary
    show_500_error_summary(customer_id)
    
    print(f"\n500 ERROR OBSERVABILITY DEMO COMPLETE!")
    print(f"Check CloudWatch logs for complete error handling trace")

if __name__ == "__main__":
    main()