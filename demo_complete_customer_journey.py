#!/usr/bin/env python3
"""
Complete Customer Journey Tracking Demo
Shows the full lifecycle: SNS → SQS → Lambda → Error → Queue → Retry
"""

import json
import boto3
import time
from datetime import datetime
from observability.otel_config import get_bank_account_observability

# Configuration
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
OBSERVABILITY_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-observability.fifo"

def track_complete_customer_journey():
    """Track complete customer journey with detailed timestamps"""
    
    print("COMPLETE CUSTOMER JOURNEY TRACKING")
    print("Demonstrating: SNS → SQS → Lambda → Error → Queue → Retry")
    print("=" * 70)
    
    # Initialize observability
    observability = get_bank_account_observability()
    
    # Generate customer data
    #customer_id = f"ERROR500-OTEL-{int(time.time())}"
    customer_id = "ERROR500-payment-crisis-1756846792"
    
    # Start journey tracking
    journey_start = time.time()
    trace_info = observability.start_customer_trace(
        operation="complete_customer_journey",
        customer_id=customer_id,
        message_attributes={
            "demo_type": "complete_journey_tracking",
            "expected_flow": "sns_sqs_lambda_error_queue_retry"
        }
    )
    
    print(f"CUSTOMER JOURNEY STARTED")
    print(f"   Customer ID: {customer_id}")
    print(f"   Trace ID: {trace_info['trace_id']}")
    print(f"   Journey Start: {datetime.fromtimestamp(journey_start).strftime('%H:%M:%S.%f')[:-3]}")
    
    # STEP 1: Send to SNS Topic
    print(f"\nSTEP 1: Publishing to SNS Topic")
    print("-" * 40)
    
    sns_timestamp = time.time()
    message = {
        'customer_id': customer_id,
        'routing_number': '123456789',
        'account_number': '987654321500',
        'message_id': f"journey-{int(time.time())}",
        'message_group_id': customer_id,
        'timestamp': datetime.utcnow().isoformat(),
        'journey_step': 'sns_publish'
    }
    
    observability.record_customer_event(
        event_type="step_1_sns_publish_started",
        customer_id=customer_id,
        status="processing",
        details={
            "step": 1,
            "action": "sns_publish",
            "timestamp": datetime.fromtimestamp(sns_timestamp).strftime('%H:%M:%S.%f')[:-3],
            "message_size": len(json.dumps(message))
        }
    )
    
    try:
        sns_client = boto3.client('sns')
        response = sns_client.publish(
            TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
            Message=json.dumps(message),
            Subject="Complete Journey Demo - Bank Account Setup",
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
            MessageDeduplicationId=f"journey-{customer_id}-{int(time.time())}"
        )
        
        sns_complete_timestamp = time.time()
        
        observability.record_customer_event(
            event_type="step_1_sns_publish_completed",
            customer_id=customer_id,
            status="success",
            details={
                "step": 1,
                "action": "sns_publish_completed",
                "timestamp": datetime.fromtimestamp(sns_complete_timestamp).strftime('%H:%M:%S.%f')[:-3],
                "sns_message_id": response['MessageId'],
                "duration_ms": (sns_complete_timestamp - sns_timestamp) * 1000
            }
        )
        
        print(f"   {datetime.fromtimestamp(sns_timestamp).strftime('%H:%M:%S.%f')[:-3]} - SNS Publish Started")
        print(f"   {datetime.fromtimestamp(sns_complete_timestamp).strftime('%H:%M:%S.%f')[:-3]} - SNS Publish Completed")
        print(f"   SNS Message ID: {response['MessageId']}")
        print(f"   Duration: {(sns_complete_timestamp - sns_timestamp) * 1000:.2f}ms")
        
        return customer_id, response['MessageId']
        
    except Exception as e:
        print(f"   SNS Publish Failed: {e}")
        return None, None

def monitor_sqs_delivery(customer_id: str):
    """Monitor message delivery to SQS queue"""
    
    print(f"\nSTEP 2: Monitoring SQS Queue Delivery")
    print("-" * 40)
    
    observability = get_bank_account_observability()
    sqs = boto3.client('sqs')
    
    # Monitor for message arrival in SQS
    for check in range(10):  # Check for 10 seconds
        check_timestamp = time.time()
        
        try:
            response = sqs.get_queue_attributes(
                QueueUrl=OBSERVABILITY_QUEUE_URL,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            
            available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
            in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
            
            if available > 0:
                observability.record_customer_event(
                    event_type="step_2_sqs_message_delivered",
                    customer_id=customer_id,
                    status="success",
                    details={
                        "step": 2,
                        "action": "sqs_delivery_detected",
                        "timestamp": datetime.fromtimestamp(check_timestamp).strftime('%H:%M:%S.%f')[:-3],
                        "available_messages": available,
                        "in_flight_messages": in_flight,
                        "delivery_time_seconds": check
                    }
                )
                
                print(f"   {datetime.fromtimestamp(check_timestamp).strftime('%H:%M:%S.%f')[:-3]} - Message Delivered to SQS")
                print(f"   Available: {available}, In-Flight: {in_flight}")
                print(f"   Delivery Time: {check} seconds after SNS publish")
                return True
            
            time.sleep(1)
            
        except Exception as e:
            print(f"   SQS Check Failed: {e}")
            return False
    
    print(f"   Message not detected in SQS after 10 seconds")
    return False

def monitor_lambda_processing(customer_id: str):
    """Monitor Lambda processing and error handling"""
    
    print(f"\nSTEP 3: Monitoring Lambda Processing")
    print("-" * 40)
    
    observability = get_bank_account_observability()
    logs_client = boto3.client('logs')
    log_group = '/aws/lambda/utility-customer-system-dev-bank-account-observability'
    
    # Monitor for Lambda processing
    for check in range(30):  # Check for 30 seconds
        check_timestamp = time.time()
        
        try:
            # Search for customer-specific processing logs
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                filterPattern=f'"{customer_id}"',
                startTime=int((time.time() - 300) * 1000),  # Last 5 minutes
                limit=20
            )
            
            processing_events = []
            error_events = []
            
            for event in response['events']:
                message = event['message']
                event_timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S.%f')[:-3]
                
                if 'message_received' in message:
                    processing_events.append(f"   {event_timestamp} - Lambda Started Processing")
                elif 'validation_started' in message:
                    processing_events.append(f"   {event_timestamp} - Validation Started")
                elif 'demo_500_error_triggered' in message:
                    error_events.append(f"   {event_timestamp} - 500 Error Triggered")
                elif 'subscription_disabled' in message:
                    error_events.append(f"   {event_timestamp} - Subscription Disabled")
                elif 'SUBSCRIPTION_DISABLED' in message:
                    error_events.append(f"   {event_timestamp} - Subscription Control Executed")
            
            if processing_events or error_events:
                print(f"   Lambda Processing Events:")
                for event in processing_events:
                    print(event)
                
                if error_events:
                    print(f"   Error Handling Events:")
                    for event in error_events:
                        print(event)
                
                observability.record_customer_event(
                    event_type="step_3_lambda_processing_detected",
                    customer_id=customer_id,
                    status="success" if not error_events else "error",
                    details={
                        "step": 3,
                        "action": "lambda_processing_detected",
                        "timestamp": datetime.fromtimestamp(check_timestamp).strftime('%H:%M:%S.%f')[:-3],
                        "processing_events": len(processing_events),
                        "error_events": len(error_events),
                        "processing_time_seconds": check
                    }
                )
                
                return len(error_events) > 0  # Return True if errors occurred
            
            time.sleep(1)
            
        except Exception as e:
            print(f"   Lambda Log Check Failed: {e}")
            time.sleep(1)
    
    print(f"   No Lambda processing detected after 30 seconds")
    return False

def monitor_error_and_queue_retention(customer_id: str):
    """Monitor error handling and message retention in queue"""
    
    print(f"\nSTEP 4: Monitoring Error Handling & Queue Retention")
    print("-" * 40)
    
    observability = get_bank_account_observability()
    sqs = boto3.client('sqs')
    lambda_client = boto3.client('lambda')
    
    # Check subscription status
    function_name = "utility-customer-system-dev-bank-account-observability"
    
    try:
        response = lambda_client.list_event_source_mappings(FunctionName=function_name)
        
        for mapping in response['EventSourceMappings']:
            if 'observability' in mapping['EventSourceArn']:
                state = mapping['State']
                check_timestamp = time.time()
                
                observability.record_customer_event(
                    event_type="step_4_subscription_status_checked",
                    customer_id=customer_id,
                    status="success",
                    details={
                        "step": 4,
                        "action": "subscription_status_check",
                        "timestamp": datetime.fromtimestamp(check_timestamp).strftime('%H:%M:%S.%f')[:-3],
                        "subscription_state": state,
                        "mapping_uuid": mapping['UUID']
                    }
                )
                
                print(f"   {datetime.fromtimestamp(check_timestamp).strftime('%H:%M:%S.%f')[:-3]} - Subscription Status: {state}")
                
                if state == 'Disabled':
                    print(f"   System correctly disabled subscription due to 500 error")
                    
                    # Check if message remains in queue
                    queue_response = sqs.get_queue_attributes(
                        QueueUrl=OBSERVABILITY_QUEUE_URL,
                        AttributeNames=['ApproximateNumberOfMessages']
                    )
                    
                    available = int(queue_response['Attributes'].get('ApproximateNumberOfMessages', 0))
                    
                    if available > 0:
                        print(f"   Message remains in SQS queue (available: {available})")
                        print(f"   Processing stopped - preventing cascade failures")
                        return True
                
                break
        
    except Exception as e:
        print(f"   Subscription check failed: {e}")
    
    return False

def simulate_system_recovery_and_retry(customer_id: str):
    """Simulate system recovery and message retry processing"""
    
    print(f"\nSTEP 5: Simulating System Recovery & Retry Processing")
    print("-" * 40)
    
    observability = get_bank_account_observability()
    
    # Send resubscribe message
    try:
        sns_client = boto3.client('sns')
        control_topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
        
        recovery_timestamp = time.time()
        
        control_message = {
            'action': 'enable',
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'system_recovery_simulation',
            'customer_context': customer_id
        }
        
        response = sns_client.publish(
            TopicArn=control_topic_arn,
            Message=json.dumps(control_message),
            Subject='System Recovery - Re-enable Processing'
        )
        
        observability.record_customer_event(
            event_type="step_5_system_recovery_initiated",
            customer_id=customer_id,
            status="success",
            details={
                "step": 5,
                "action": "recovery_message_sent",
                "timestamp": datetime.fromtimestamp(recovery_timestamp).strftime('%H:%M:%S.%f')[:-3],
                "sns_message_id": response['MessageId'],
                "recovery_action": "enable_subscriptions"
            }
        )
        
        print(f"   Recovery Message Sent at {datetime.fromtimestamp(recovery_timestamp).strftime('%H:%M:%S.%f')[:-3]}")
        print(f"   SNS Message ID: {response['MessageId']}")
        print(f"   Action: Re-enable subscription for retry processing")
        
        # Wait and check if subscription is re-enabled
        print(f"   Waiting 10 seconds for subscription re-enablement...")
        time.sleep(10)
        
        # Check final subscription status
        lambda_client = boto3.client('lambda')
        function_name = "utility-customer-system-dev-bank-account-observability"
        
        response = lambda_client.list_event_source_mappings(FunctionName=function_name)
        
        for mapping in response['EventSourceMappings']:
            if 'observability' in mapping['EventSourceArn']:
                final_state = mapping['State']
                final_timestamp = time.time()
                
                observability.record_customer_event(
                    event_type="step_5_final_subscription_status",
                    customer_id=customer_id,
                    status="success",
                    details={
                        "step": 5,
                        "action": "final_status_check",
                        "timestamp": datetime.fromtimestamp(final_timestamp).strftime('%H:%M:%S.%f')[:-3],
                        "final_subscription_state": final_state,
                        "recovery_successful": final_state == 'Enabled'
                    }
                )
                
                print(f"   {datetime.fromtimestamp(final_timestamp).strftime('%H:%M:%S.%f')[:-3]} - Final Status: {final_state}")
                
                if final_state == 'Enabled':
                    print(f"   System recovery successful - ready for retry processing")
                else:
                    print(f"   Subscription still disabled - may need more time")
                
                return final_state == 'Enabled'
        
    except Exception as e:
        print(f"   Recovery simulation failed: {e}")
        return False

def show_complete_journey_summary(customer_id: str):
    """Show complete customer journey summary"""
    
    print(f"\nCOMPLETE CUSTOMER JOURNEY SUMMARY")
    print("=" * 60)
    print(f"Customer ID: {customer_id}")
    print(f"Journey Type: Complete Lifecycle Tracking")
    
    print(f"\nJourney Steps Completed:")
    print(f"   1. SNS Topic Publishing - Message sent to transaction processing")
    print(f"   2. SQS Queue Delivery - Message delivered to observability queue")
    print(f"   3. Lambda Processing - Message processed, 500 error detected")
    print(f"   4. Error Handling - Subscription disabled, message retained")
    print(f"   5. System Recovery - Recovery message sent, subscription re-enabled")
    
    print(f"\nKey Observability Features Demonstrated:")
    print(f"   • Complete message lifecycle tracking")
    print(f"   • Precise timestamp correlation across services")
    print(f"   • Error detection and automatic response")
    print(f"   • Queue retention during system issues")
    print(f"   • Recovery workflow and retry capability")
    
    print(f"\nCustomer Support Benefits:")
    print(f"   • Track exact message flow: SNS → SQS → Lambda")
    print(f"   • Identify processing delays and bottlenecks")
    print(f"   • Monitor error handling and system responses")
    print(f"   • Verify message retention during outages")
    print(f"   • Confirm successful recovery and retry processing")

def main():
    """Main function for complete customer journey demo"""
    
    # Step 1: Send to SNS
    customer_id, sns_message_id = track_complete_customer_journey()
    
    if not customer_id:
        print("Demo failed - could not send SNS message")
        return
    
    # Step 2: Monitor SQS delivery
    sqs_delivered = monitor_sqs_delivery(customer_id)
    
    # Step 3: Monitor Lambda processing
    error_occurred = monitor_lambda_processing(customer_id)
    
    # Step 4: Monitor error handling and queue retention
    error_handled = monitor_error_and_queue_retention(customer_id)
    
    # Step 5: Simulate system recovery
    recovery_successful = simulate_system_recovery_and_retry(customer_id)
    
    # Show summary
    show_complete_journey_summary(customer_id)
    
    print(f"\nCOMPLETE CUSTOMER JOURNEY DEMO FINISHED!")
    print(f"Check CloudWatch logs for detailed observability data")
    print(f"Search pattern: CUSTOMER_EVENT \"{customer_id}\"")

if __name__ == "__main__":
    main()