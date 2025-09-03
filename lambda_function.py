#!/usr/bin/env python3
"""
Instrumented Bank Account Setup Lambda Function
Comprehensive observability for customer journey tracking
"""

import json
import time
import boto3
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

# Add observability to path
sys.path.append('/opt/python')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from observability.otel_config import get_bank_account_observability

# Initialize observability
observability = get_bank_account_observability()

def lambda_handler(event, context):
    """
    Main Lambda handler with comprehensive observability
    Handles both SQS messages and SNS subscription control messages
    """
    
    try:
        # Check if this is an SNS subscription control message
        if 'Records' in event and event['Records'][0].get('EventSource') == 'aws:sns':
            observability.record_customer_event(
                event_type="sns_subscription_control_received",
                customer_id="system",
                status="processing",
                details={"event_source": "aws:sns"}
            )
            
            # Extract SNS message
            sns_record = event['Records'][0]
            sns_message = json.loads(sns_record['Sns']['Message'])
            
            # Handle subscription control
            handle_subscription_control(sns_message, sns_message.get('customer_context', 'system'))
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Subscription control processed',
                    'success': True
                })
            }
        
        # Handle SQS messages (bank account setup requests)
        elif 'Records' in event:
            for record in event.get('Records', []):
                if record.get('eventSource') == 'aws:sqs':
                    process_bank_account_message(record, context)
        
        # Direct invocation (for testing)
        else:
            # Create a mock SQS record for direct invocation
            mock_record = {
                'body': json.dumps(event),
                'eventSource': 'aws:sqs',
                'messageId': 'direct-invocation'
            }
            process_bank_account_message(mock_record, context)
    
    except Exception as e:
        observability.record_error(
            error_type="lambda_handler_error",
            customer_id="system",
            error_message=f"Lambda handler failed: {str(e)}"
        )
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    
    return {'statusCode': 200, 'body': 'Processing complete'}

def process_bank_account_message(record: Dict, context: Any):
    """
    Process individual bank account setup message with full observability
    
    Args:
        record: SQS record containing the message
        context: Lambda context
    """
    start_time = time.time()
    customer_id = None
    
    try:
        # Extract message details
        message_body = json.loads(record['body'])
        
        # Check if this is an SNS message (subscription control)
        if 'Message' in message_body and 'Subject' in message_body:
            # This is an SNS message - check if it's a control message
            sns_message = json.loads(message_body['Message'])
            if 'action' in sns_message and sns_message.get('action') in ['enable', 'disable']:
                customer_id = sns_message.get('customer_context', 'system')
                observability.record_customer_event(
                    event_type="subscription_control_message_received",
                    customer_id=customer_id,
                    status="processing",
                    details={
                        "action": sns_message.get('action'),
                        "source": sns_message.get('source', 'unknown'),
                        "message_type": "sns_control"
                    }
                )
                handle_subscription_control(sns_message, customer_id)
                return  # Exit early for control messages
        
        customer_id = message_body.get('customer_id', 'unknown')
        
        # Start customer trace
        trace_info = observability.start_customer_trace(
            operation="bank_account_setup",
            customer_id=customer_id,
            message_attributes={
                "routing_number": message_body.get('routing_number', ''),
                "message_id": message_body.get('message_id', ''),
                "sqs_message_id": record.get('messageId', ''),
                "receipt_handle": record.get('receiptHandle', '')[:20] + "..."
            }
        )
        
        # Record message received event
        observability.record_customer_event(
            event_type="message_received",
            customer_id=customer_id,
            status="processing",
            details={
                "source": "sqs",
                "queue_name": extract_queue_name(record.get('eventSourceARN', '')),
                "message_size": len(json.dumps(message_body)),
                "lambda_request_id": getattr(context, 'aws_request_id', 'unknown')
            }
        )
        
        # Validate message format
        validation_result = validate_bank_account_message(message_body, customer_id)
        if not validation_result["valid"]:
            raise ValueError(f"Validation failed: {validation_result['error']}")
        
        # Check for intentional errors (demo purposes)
        if "ERROR500" in customer_id:
            simulate_500_error(customer_id)
        elif "ERROR400" in customer_id:
            simulate_400_error(customer_id)
        
        # Process bank account setup
        setup_result = setup_bank_account(message_body, customer_id)
        
        # Record successful completion
        duration_ms = (time.time() - start_time) * 1000
        
        observability.record_customer_event(
            event_type="bank_account_setup_completed",
            customer_id=customer_id,
            status="success",
            details={
                "account_id": setup_result.get("account_id"),
                "processing_duration_ms": duration_ms,
                "validation_checks_passed": setup_result.get("validation_checks", 0)
            }
        )
        
        observability.record_processing_duration(
            operation="bank_account_setup",
            duration_ms=duration_ms,
            customer_id=customer_id,
            status="success"
        )
        
        observability.end_customer_trace(
            customer_id=customer_id,
            status="success",
            duration_ms=duration_ms
        )
        
    except Exception as e:
        # Record error with full context
        duration_ms = (time.time() - start_time) * 1000
        error_type = classify_error(e)
        
        observability.record_error(
            error_type=error_type,
            customer_id=customer_id or "unknown",
            error_message=str(e),
            additional_context={
                "processing_duration_ms": duration_ms,
                "lambda_request_id": getattr(context, 'aws_request_id', 'unknown'),
                "error_class": e.__class__.__name__,
                "stack_trace": str(e)[:500]  # Truncated for logging
            }
        )
        
        observability.record_processing_duration(
            operation="bank_account_setup",
            duration_ms=duration_ms,
            customer_id=customer_id or "unknown",
            status="error"
        )
        
        observability.end_customer_trace(
            customer_id=customer_id or "unknown",
            status="error",
            duration_ms=duration_ms
        )
        
        # Handle error based on type
        if error_type == "external_service_error":
            handle_500_error(customer_id or "unknown", str(e))
        else:
            # Re-raise for Lambda to handle
            raise

def validate_bank_account_message(message: Dict, customer_id: str) -> Dict[str, Any]:
    """
    Validate bank account message with observability
    
    Args:
        message: Message to validate
        customer_id: Customer identifier
    
    Returns:
        Validation result with details
    """
    observability.record_customer_event(
        event_type="validation_started",
        customer_id=customer_id,
        status="processing",
        details={"validation_type": "bank_account_message"}
    )
    
    required_fields = ['customer_id', 'routing_number', 'account_number']
    missing_fields = [field for field in required_fields if not message.get(field)]
    
    if missing_fields:
        observability.record_customer_event(
            event_type="validation_failed",
            customer_id=customer_id,
            status="error",
            details={
                "missing_fields": missing_fields,
                "validation_type": "required_fields"
            }
        )
        return {"valid": False, "error": f"Missing required fields: {missing_fields}"}
    
    # Validate routing number format
    routing_number = message.get('routing_number', '')
    if not routing_number.isdigit() or len(routing_number) != 9:
        observability.record_customer_event(
            event_type="validation_failed",
            customer_id=customer_id,
            status="error",
            details={
                "field": "routing_number",
                "value": routing_number[:4] + "****",  # Masked for security
                "validation_type": "format_check"
            }
        )
        return {"valid": False, "error": "Invalid routing number format"}
    
    observability.record_customer_event(
        event_type="validation_completed",
        customer_id=customer_id,
        status="success",
        details={"validation_checks_passed": 2}
    )
    
    return {"valid": True, "checks_passed": 2}

def setup_bank_account(message: Dict, customer_id: str) -> Dict[str, Any]:
    """
    Setup bank account with external service calls and observability
    
    Args:
        message: Bank account message
        customer_id: Customer identifier
    
    Returns:
        Setup result with account details
    """
    observability.record_customer_event(
        event_type="bank_setup_started",
        customer_id=customer_id,
        status="processing",
        details={
            "routing_number": message['routing_number'][:4] + "****",
            "account_number": "****" + message['account_number'][-4:]
        }
    )
    
    # Simulate external bank validation service call
    validation_start = time.time()
    bank_validation_result = call_bank_validation_service(message, customer_id)
    validation_duration = (time.time() - validation_start) * 1000
    
    observability.record_customer_event(
        event_type="external_validation_completed",
        customer_id=customer_id,
        status="success" if bank_validation_result["valid"] else "error",
        details={
            "service": "bank_validation_api",
            "duration_ms": validation_duration,
            "validation_score": bank_validation_result.get("score", 0)
        }
    )
    
    # Create account record
    account_id = f"BA-{customer_id}-{int(time.time())}"
    
    observability.record_customer_event(
        event_type="account_created",
        customer_id=customer_id,
        status="success",
        details={
            "account_id": account_id,
            "account_type": "checking",
            "status": "active"
        }
    )
    
    return {
        "account_id": account_id,
        "status": "active",
        "validation_checks": 3,
        "created_at": datetime.utcnow().isoformat()
    }

def call_bank_validation_service(message: Dict, customer_id: str) -> Dict[str, Any]:
    """
    Simulate external bank validation service call
    
    Args:
        message: Bank account message
        customer_id: Customer identifier
    
    Returns:
        Validation result from external service
    """
    # Simulate API call delay
    time.sleep(0.1)
    
    # Simulate validation logic
    routing_number = message.get('routing_number', '')
    
    # Mock validation based on routing number
    if routing_number.startswith('123'):
        return {"valid": True, "score": 95, "bank_name": "Demo Bank"}
    elif routing_number.startswith('999'):
        return {"valid": False, "score": 0, "error": "Invalid bank"}
    else:
        return {"valid": True, "score": 85, "bank_name": "Generic Bank"}

def simulate_500_error(customer_id: str):
    """Simulate 500 error for demo purposes"""
    observability.record_customer_event(
        event_type="demo_500_error_triggered",
        customer_id=customer_id,
        status="error",
        details={"error_type": "simulated", "demo_scenario": True}
    )
    raise Exception("Bank validation service unavailable (500 error simulation)")

def simulate_400_error(customer_id: str):
    """Simulate 400 error for demo purposes"""
    observability.record_customer_event(
        event_type="demo_400_error_triggered",
        customer_id=customer_id,
        status="error",
        details={"error_type": "simulated", "demo_scenario": True}
    )
    raise ValueError("Invalid account information provided (400 error simulation)")

def classify_error(error: Exception) -> str:
    """
    Classify error type for proper handling
    
    Args:
        error: Exception that occurred
    
    Returns:
        Error classification
    """
    error_message = str(error).lower()
    
    if "unavailable" in error_message or "500" in error_message:
        return "external_service_error"
    elif "invalid" in error_message or "400" in error_message:
        return "validation_error"
    elif "timeout" in error_message:
        return "timeout_error"
    else:
        return "system_error"

def handle_500_error(customer_id: str, error_message: str):
    """
    Handle 500 errors by disabling subscriptions
    
    Args:
        customer_id: Customer identifier
        error_message: Error description
    """
    try:
        observability.record_customer_event(
            event_type="500_error_detected",
            customer_id=customer_id,
            status="error",
            details={
                "error_message": error_message,
                "action": "disabling_subscription",
                "service": "bank_account_setup"
            }
        )
        
        # Disable the current Lambda's SQS event source mapping
        lambda_client = boto3.client('lambda')
        function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'utility-customer-system-dev-bank-account-observability')
        
        # List event source mappings for this function
        response = lambda_client.list_event_source_mappings(FunctionName=function_name)
        
        for mapping in response['EventSourceMappings']:
            if 'sqs' in mapping['EventSourceArn'].lower() and mapping['State'] == 'Enabled':
                # Disable the mapping
                lambda_client.update_event_source_mapping(
                    UUID=mapping['UUID'],
                    Enabled=False
                )
                
                observability.record_customer_event(
                    event_type="subscription_disabled",
                    customer_id=customer_id,
                    status="success",
                    details={
                        "reason": "500_error_threshold_reached",
                        "service": "bank_account_setup",
                        "mapping_uuid": mapping['UUID'],
                        "event_source_arn": mapping['EventSourceArn']
                    }
                )
                
                print(f"SUBSCRIPTION_DISABLED: {mapping['UUID']} due to 500 error for customer {customer_id}")
                break
        
        # Send error notification to SNS for monitoring
        try:
            sns_client = boto3.client('sns')
            error_topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
            
            error_notification = {
                "error_type": "500_error",
                "customer_id": customer_id,
                "service": "bank_account_setup",
                "error_message": error_message,
                "action_taken": "subscription_disabled",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            sns_client.publish(
                TopicArn=error_topic_arn,
                Message=json.dumps(error_notification),
                Subject="500 Error - Subscription Disabled"
            )
            
            observability.record_customer_event(
                event_type="error_notification_sent",
                customer_id=customer_id,
                status="success",
                details={
                    "notification_type": "500_error",
                    "topic_arn": error_topic_arn.split(':')[-1]
                }
            )
            
        except Exception as sns_error:
            observability.record_error(
                error_type="notification_error",
                customer_id=customer_id,
                error_message=f"Failed to send error notification: {str(sns_error)}"
            )
        
    except Exception as e:
        observability.record_error(
            error_type="system_error",
            customer_id=customer_id,
            error_message=f"Failed to handle 500 error: {str(e)}"
        )

def handle_subscription_control(control_message: Dict[str, Any], customer_id: str = "system"):
    """
    Handle subscription control messages (enable/disable)
    
    Args:
        control_message: Control message with action
        customer_id: Customer identifier for logging
    """
    try:
        action = control_message.get('action', '').lower()
        
        observability.record_customer_event(
            event_type="subscription_control_received",
            customer_id=customer_id,
            status="processing",
            details={
                "action": action,
                "source": control_message.get('source', 'unknown')
            }
        )
        
        if action == 'enable':
            # Re-enable the Lambda's SQS event source mapping
            lambda_client = boto3.client('lambda')
            function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'utility-customer-system-dev-bank-account-observability')
            
            response = lambda_client.list_event_source_mappings(FunctionName=function_name)
            
            for mapping in response['EventSourceMappings']:
                if 'sqs' in mapping['EventSourceArn'].lower() and mapping['State'] == 'Disabled':
                    # Enable the mapping
                    lambda_client.update_event_source_mapping(
                        UUID=mapping['UUID'],
                        Enabled=True
                    )
                    
                    observability.record_customer_event(
                        event_type="subscription_enabled",
                        customer_id=customer_id,
                        status="success",
                        details={
                            "reason": "control_message_received",
                            "service": "bank_account_setup",
                            "mapping_uuid": mapping['UUID'],
                            "event_source_arn": mapping['EventSourceArn']
                        }
                    )
                    
                    print(f"SUBSCRIPTION_ENABLED: {mapping['UUID']} via control message")
                    break
        
        elif action == 'disable':
            # Disable subscriptions (similar to 500 error handling)
            handle_500_error(customer_id, "Manual disable via control message")
        
    except Exception as e:
        observability.record_error(
            error_type="subscription_control_error",
            customer_id=customer_id,
            error_message=f"Failed to handle subscription control: {str(e)}"
        )

def extract_queue_name(event_source_arn: str) -> str:
    """Extract queue name from SQS ARN"""
    try:
        return event_source_arn.split(':')[-1]
    except:
        return "unknown_queue"