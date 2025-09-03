#!/usr/bin/env python3
"""
Demo: OpenTelemetry Observability for Bank Account Setup
Shows comprehensive customer journey tracking from SNS to Lambda completion
"""

import json
import boto3
import time
from datetime import datetime
from observability.otel_config import get_bank_account_observability

# Configuration
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"

def send_instrumented_bank_account_message():
    """Send bank account message with observability tracking"""
    
    print("OBSERVABILITY DEMO - Bank Account Setup")
    print("Tracking customer journey from SNS to Lambda completion")
    print("=" * 60)
    
    # Initialize observability
    observability = get_bank_account_observability()
    
    # Generate customer data
    customer_id = f"DEMO-OTEL-{int(time.time())}"
    
    # Start customer journey trace
    trace_info = observability.start_customer_trace(
        operation="bank_account_journey",
        customer_id=customer_id,
        message_attributes={
            "demo_type": "observability_showcase",
            "expected_flow": "sns_to_sqs_to_lambda"
        }
    )
    
    print(f"Started Customer Journey Trace:")
    print(f"  Customer ID: {customer_id}")
    print(f"  Trace ID: {trace_info['trace_id']}")
    print(f"  Span ID: {trace_info['span_id']}")
    
    # Record journey start
    observability.record_customer_event(
        event_type="customer_journey_started",
        customer_id=customer_id,
        status="processing",
        details={
            "channel": "demo_script",
            "journey_type": "bank_account_setup",
            "expected_steps": ["sns_publish", "sqs_delivery", "lambda_processing", "account_creation"]
        }
    )
    
    # Create message
    message = {
        'customer_id': customer_id,
        'routing_number': '123456789',
        'account_number': '987654321001',
        'message_id': f"demo-otel-{int(time.time())}",
        'message_group_id': customer_id,
        'timestamp': datetime.utcnow().isoformat(),
        'demo_observability': True
    }
    
    # Send to SNS with observability
    sns_start_time = time.time()
    
    observability.record_customer_event(
        event_type="sns_publish_started",
        customer_id=customer_id,
        status="processing",
        details={
            "topic_arn": TRANSACTION_PROCESSING_TOPIC_ARN.split(':')[-1],
            "message_size": len(json.dumps(message)),
            "target_lambda": "observability_demo_lambda"
        }
    )
    
    try:
        sns_client = boto3.client('sns')
        response = sns_client.publish(
            TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
            Message=json.dumps(message),
            Subject="Observability Demo - Bank Account Setup",
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
            MessageDeduplicationId=f"demo-otel-{customer_id}-{int(time.time())}"
        )
        
        sns_duration = (time.time() - sns_start_time) * 1000
        
        observability.record_customer_event(
            event_type="sns_publish_completed",
            customer_id=customer_id,
            status="success",
            details={
                "sns_message_id": response['MessageId'],
                "duration_ms": sns_duration
            }
        )
        
        observability.record_processing_duration(
            operation="sns_publish",
            duration_ms=sns_duration,
            customer_id=customer_id,
            status="success"
        )
        
        print(f"\nSNS Message Published Successfully:")
        print(f"  SNS Message ID: {response['MessageId']}")
        print(f"  Duration: {sns_duration:.2f}ms")
        
        return customer_id, response['MessageId']
        
    except Exception as e:
        sns_duration = (time.time() - sns_start_time) * 1000
        
        observability.record_error(
            error_type="sns_publish_error",
            customer_id=customer_id,
            error_message=str(e),
            additional_context={
                "duration_ms": sns_duration,
                "topic_arn": TRANSACTION_PROCESSING_TOPIC_ARN
            }
        )
        
        print(f"SNS Publish Failed: {e}")
        return None, None

def monitor_customer_journey(customer_id: str, sns_message_id: str):
    """Monitor the customer journey through the system"""
    
    print(f"\nMonitoring Customer Journey:")
    print(f"  Customer ID: {customer_id}")
    print(f"  SNS Message ID: {sns_message_id}")
    print("-" * 40)
    
    observability = get_bank_account_observability()
    
    # Monitor for 60 seconds
    for check in range(12):  # 12 checks, 5 seconds apart
        print(f"\nCheck {check + 1}/12 (after {check * 5} seconds):")
        
        # Record monitoring event
        observability.record_customer_event(
            event_type="journey_monitoring_check",
            customer_id=customer_id,
            status="processing",
            details={
                "check_number": check + 1,
                "elapsed_seconds": check * 5
            }
        )
        
        # Check SQS queue for message
        check_sqs_status(customer_id)
        
        # Check Lambda logs for processing
        check_lambda_processing(customer_id)
        
        if check < 11:  # Don't sleep on last iteration
            time.sleep(5)
    
    # End journey monitoring
    observability.record_customer_event(
        event_type="journey_monitoring_completed",
        customer_id=customer_id,
        status="success",
        details={
            "total_checks": 12,
            "monitoring_duration_seconds": 60
        }
    )

def check_sqs_status(customer_id: str):
    """Check SQS queue status for customer message"""
    
    observability = get_bank_account_observability()
    
    try:
        sqs = boto3.client('sqs')
        queue_url = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-observability.fifo"
        
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        
        available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
        in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
        
        print(f"  SQS Queue Status: {available} available, {in_flight} in-flight")
        
        observability.record_customer_event(
            event_type="sqs_status_checked",
            customer_id=customer_id,
            status="success",
            details={
                "available_messages": available,
                "in_flight_messages": in_flight,
                "queue_name": "bank-account-setup"
            }
        )
        
    except Exception as e:
        observability.record_error(
            error_type="sqs_monitoring_error",
            customer_id=customer_id,
            error_message=str(e)
        )
        print(f"  SQS Check Failed: {e}")

def check_lambda_processing(customer_id: str):
    """Check Lambda logs for customer processing"""
    
    observability = get_bank_account_observability()
    
    try:
        logs_client = boto3.client('logs')
        log_group = '/aws/lambda/utility-customer-system-dev-bank-account-observability'
        
        # Search for customer-specific logs
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            filterPattern=f'"{customer_id}"',
            startTime=int((time.time() - 300) * 1000),  # Last 5 minutes
            limit=10
        )
        
        if response['events']:
            print(f"  Lambda Processing: Found {len(response['events'])} log entries")
            
            # Look for specific events
            for event in response['events']:
                message = event['message']
                if 'CUSTOMER_EVENT' in message:
                    try:
                        event_data = json.loads(message.split('CUSTOMER_EVENT: ')[1])
                        print(f"    Event: {event_data.get('event_type')} - {event_data.get('status')}")
                    except:
                        pass
                elif 'CUSTOMER_ERROR' in message:
                    print(f"    Error detected in processing")
            
            observability.record_customer_event(
                event_type="lambda_processing_detected",
                customer_id=customer_id,
                status="success",
                details={
                    "log_entries_found": len(response['events']),
                    "log_group": log_group
                }
            )
        else:
            print(f"  Lambda Processing: No logs found yet")
            
    except Exception as e:
        observability.record_error(
            error_type="lambda_monitoring_error",
            customer_id=customer_id,
            error_message=str(e)
        )
        print(f"  Lambda Check Failed: {e}")

def show_observability_summary(customer_id: str):
    """Show summary of observability data collected"""
    
    print(f"\nOBSERVABILITY SUMMARY")
    print("=" * 40)
    print(f"Customer ID: {customer_id}")
    print(f"Journey Type: Bank Account Setup")
    print(f"Observability Features Demonstrated:")
    print(f"  - Customer journey tracing")
    print(f"  - Structured event logging")
    print(f"  - Error tracking and classification")
    print(f"  - Performance metrics collection")
    print(f"  - Cross-service correlation")
    print(f"  - Real-time monitoring")
    
    print(f"\nFor Customer Support:")
    print(f"  1. Search CloudWatch logs for: {customer_id}")
    print(f"  2. Filter by event types: CUSTOMER_EVENT, CUSTOMER_ERROR, CUSTOMER_METRIC")
    print(f"  3. Track journey from SNS -> SQS -> Lambda -> Account Creation")
    print(f"  4. Identify bottlenecks and errors with precise timestamps")

def main():
    """Main demo function"""
    
    # Send message with observability
    customer_id, sns_message_id = send_instrumented_bank_account_message()
    
    if not customer_id:
        print("Demo failed - could not send message")
        return
    
    # Monitor customer journey
    monitor_customer_journey(customer_id, sns_message_id)
    
    # Show observability summary
    show_observability_summary(customer_id)
    
    print(f"\nOBSERVABILITY DEMO COMPLETE!")
    print(f"Check CloudWatch logs for detailed customer journey tracking")

if __name__ == "__main__":
    main()