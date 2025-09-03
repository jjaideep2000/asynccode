#!/usr/bin/env python3
"""
Deploy Instrumented Lambda Functions
Updates existing Lambda functions with observability-enabled code
"""

import boto3
import json
import zipfile
import os
import tempfile
from datetime import datetime

def create_instrumented_bank_account_lambda():
    """Create instrumented bank account Lambda function code"""
    
    code = '''#!/usr/bin/env python3
"""
Instrumented Bank Account Setup Lambda Function
Includes comprehensive observability for customer journey tracking
"""

import json
import time
import boto3
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Simplified observability (inline to avoid dependencies)
class SimpleObservability:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.current_trace_id = None
        self.current_span_id = None
        
    def generate_trace_id(self) -> str:
        return f"trace-{int(time.time() * 1000000)}"
    
    def generate_span_id(self) -> str:
        return f"span-{int(time.time() * 1000000)}"
    
    def start_customer_trace(self, operation: str, customer_id: str, message_attributes: Optional[Dict] = None) -> Dict[str, str]:
        self.current_trace_id = self.generate_trace_id()
        self.current_span_id = self.generate_span_id()
        
        trace_info = {
            "trace_id": self.current_trace_id,
            "span_id": self.current_span_id,
            "operation": operation,
            "customer_id": customer_id,
            "service": self.service_name,
            "start_time": datetime.utcnow().isoformat()
        }
        
        if message_attributes:
            trace_info["message_attributes"] = message_attributes
        
        self.record_customer_event(
            event_type="trace_started",
            customer_id=customer_id,
            status="processing",
            details={
                "trace_id": self.current_trace_id,
                "span_id": self.current_span_id,
                "operation": operation
            }
        )
        
        return trace_info
    
    def record_customer_event(self, event_type: str, customer_id: str, status: str, details: Optional[Dict] = None):
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "customer_id": customer_id,
            "status": status,
            "service": self.service_name
        }
        
        if details:
            event_data.update(details)
        
        if self.current_trace_id:
            event_data["trace_id"] = self.current_trace_id
            event_data["span_id"] = self.current_span_id
        
        print(f"CUSTOMER_EVENT: {json.dumps(event_data)}")
    
    def record_error(self, error_type: str, customer_id: str, error_message: str, additional_context: Optional[Dict] = None):
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "customer_id": customer_id,
            "error_message": error_message,
            "service": self.service_name,
            "trace_id": self.current_trace_id,
            "span_id": self.current_span_id
        }
        
        if additional_context:
            error_data.update(additional_context)
        
        print(f"CUSTOMER_ERROR: {json.dumps(error_data)}")
    
    def record_processing_duration(self, operation: str, duration_ms: float, customer_id: str, status: str):
        duration_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "metric_type": "processing_duration",
            "operation": operation,
            "duration_ms": duration_ms,
            "customer_id": customer_id,
            "status": status,
            "service": self.service_name,
            "trace_id": self.current_trace_id
        }
        
        print(f"CUSTOMER_METRIC: {json.dumps(duration_data)}")

# Initialize observability
observability = SimpleObservability("bank-account-service")

def lambda_handler(event, context):
    """Main Lambda handler with comprehensive observability"""
    
    try:
        # Check if this is an SNS subscription control message
        if 'Records' in event and event['Records'][0].get('EventSource') == 'aws:sns':
            observability.record_customer_event(
                event_type="sns_subscription_control_received",
                customer_id="system",
                status="processing",
                details={"event_source": "aws:sns"}
            )
            
            sns_record = event['Records'][0]
            sns_message = json.loads(sns_record['Sns']['Message'])
            
            handle_subscription_control(sns_message, sns_message.get('customer_context', 'system'))
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Subscription control processed', 'success': True})
            }
        
        # Handle SQS messages (bank account setup requests)
        elif 'Records' in event:
            for record in event.get('Records', []):
                if record.get('eventSource') == 'aws:sqs':
                    process_bank_account_message(record, context)
        
        # Direct invocation (for testing)
        else:
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
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
    
    return {'statusCode': 200, 'body': 'Processing complete'}

def process_bank_account_message(record: Dict, context: Any):
    """Process individual bank account setup message with full observability"""
    start_time = time.time()
    customer_id = None
    
    try:
        message_body = json.loads(record['body'])
        
        # Check if this is an SNS message
        if 'Message' in message_body and 'Subject' in message_body:
            sns_message = json.loads(message_body['Message'])
            
            # Check if it's a subscription control message
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
                return
            
            # Regular SNS message - use the inner message as the actual data
            message_body = sns_message
        
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
        
    except Exception as e:
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
                "stack_trace": str(e)[:500]
            }
        )
        
        observability.record_processing_duration(
            operation="bank_account_setup",
            duration_ms=duration_ms,
            customer_id=customer_id or "unknown",
            status="error"
        )
        
        if error_type == "external_service_error":
            handle_500_error(customer_id or "unknown", str(e))
        else:
            raise

def validate_bank_account_message(message: Dict, customer_id: str) -> Dict[str, Any]:
    """Validate bank account message with observability"""
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
            details={"missing_fields": missing_fields, "validation_type": "required_fields"}
        )
        return {"valid": False, "error": f"Missing required fields: {missing_fields}"}
    
    routing_number = message.get('routing_number', '')
    if not routing_number.isdigit() or len(routing_number) != 9:
        observability.record_customer_event(
            event_type="validation_failed",
            customer_id=customer_id,
            status="error",
            details={"field": "routing_number", "value": routing_number[:4] + "****", "validation_type": "format_check"}
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
    """Setup bank account with external service calls and observability"""
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
    
    account_id = f"BA-{customer_id}-{int(time.time())}"
    
    observability.record_customer_event(
        event_type="account_created",
        customer_id=customer_id,
        status="success",
        details={"account_id": account_id, "account_type": "checking", "status": "active"}
    )
    
    return {
        "account_id": account_id,
        "status": "active",
        "validation_checks": 3,
        "created_at": datetime.utcnow().isoformat()
    }

def call_bank_validation_service(message: Dict, customer_id: str) -> Dict[str, Any]:
    """Simulate external bank validation service call"""
    time.sleep(0.1)  # Simulate API call delay
    
    routing_number = message.get('routing_number', '')
    
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
    """Classify error type for proper handling"""
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
    """Handle 500 errors by disabling subscriptions"""
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
        
        lambda_client = boto3.client('lambda')
        function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'utility-customer-system-dev-bank-account-setup')
        
        response = lambda_client.list_event_source_mappings(FunctionName=function_name)
        
        for mapping in response['EventSourceMappings']:
            if 'sqs' in mapping['EventSourceArn'].lower() and mapping['State'] == 'Enabled':
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
        
    except Exception as e:
        observability.record_error(
            error_type="system_error",
            customer_id=customer_id,
            error_message=f"Failed to handle 500 error: {str(e)}"
        )

def handle_subscription_control(control_message: Dict[str, Any], customer_id: str = "system"):
    """Handle subscription control messages (enable/disable)"""
    try:
        action = control_message.get('action', '').lower()
        
        observability.record_customer_event(
            event_type="subscription_control_received",
            customer_id=customer_id,
            status="processing",
            details={"action": action, "source": control_message.get('source', 'unknown')}
        )
        
        if action == 'enable':
            lambda_client = boto3.client('lambda')
            function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'utility-customer-system-dev-bank-account-setup')
            
            response = lambda_client.list_event_source_mappings(FunctionName=function_name)
            
            for mapping in response['EventSourceMappings']:
                if 'sqs' in mapping['EventSourceArn'].lower() and mapping['State'] == 'Disabled':
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
'''
    
    return code

def deploy_lambda_function(function_name: str, code: str):
    """Deploy Lambda function with new code"""
    
    print(f"Deploying {function_name}...")
    
    lambda_client = boto3.client('lambda')
    
    # Create a temporary zip file
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            zip_file.writestr('lambda_function.py', code)
        
        # Read the zip file
        with open(temp_zip.name, 'rb') as zip_data:
            zip_bytes = zip_data.read()
        
        try:
            # Update the function code
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_bytes
            )
            
            print(f"OK {function_name} updated successfully")
            print(f"   Version: {response['Version']}")
            print(f"   Last Modified: {response['LastModified']}")
            
            return True
            
        except Exception as e:
            print(f"ERROR Failed to update {function_name}: {e}")
            return False
        
        finally:
            # Clean up temp file
            os.unlink(temp_zip.name)

def main():
    """Main deployment function"""
    
    print("DEPLOYING INSTRUMENTED LAMBDA FUNCTIONS")
    print("=" * 60)
    print("This will update your Lambda functions with observability-enabled code")
    print()
    
    # Deploy bank account setup function
    bank_account_code = create_instrumented_bank_account_lambda()
    success = deploy_lambda_function('utility-customer-system-dev-bank-account-setup', bank_account_code)
    
    if success:
        print("\nDEPLOYMENT COMPLETE!")
        print("=" * 30)
        print("Your Lambda functions now include comprehensive observability!")
        print()
        print("Next steps:")
        print("1. Run your demo_5 sequence")
        print("2. Run 'python3 reveal_observability_magic.py' to see the data")
        print()
        print("The observability system will now capture:")
        print("- Customer events")
        print("- Error events") 
        print("- Performance metrics")
        print("- System protection events")
        
    else:
        print("\nDEPLOYMENT FAILED")
        print("Please check the error messages above and try again")

if __name__ == "__main__":
    main()