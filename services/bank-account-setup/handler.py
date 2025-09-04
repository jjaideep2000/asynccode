"""
Bank Account Setup Lambda Handler
Processes bank account setup requests from utility customers
Updated: Testing incremental build system
"""

import json
import os
import time
import random
import logging
from typing import Dict, Any, List
from datetime import datetime

# Import proper error handler
try:
    from error_handler import create_error_handler
except ImportError as e:
    # Fallback - create no-op implementation
    print(f"Warning: Could not import error handler: {e}")
    def create_error_handler(service_name):
        class NoOpErrorHandler:
            def handle_error(self, error, message_body, status_code=None):
                return {
                    'action': 'continue',
                    'error_info': {'error_type': 'client_error' if status_code == 400 else 'server_error'}
                }
        return NoOpErrorHandler()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_NAME = "bank-account-setup"

# Initialize simplified error handler (no subscription control)
error_handler = create_error_handler(SERVICE_NAME)

def simulate_bank_account_validation(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate bank account validation process
    Returns validation result with potential errors for testing
    """
    
    customer_id = account_data.get('customer_id', 'unknown')
    routing_number = account_data.get('routing_number', '')
    account_number = account_data.get('account_number', '')
    
    # Simulate processing time
    processing_time = random.uniform(0.1, 2.0)
    time.sleep(processing_time)
    
    # Simulate different scenarios based on customer ID
    if 'ERROR400' in customer_id.upper():
        # Simulate 400 error (invalid account format)
        raise Exception("Invalid account number format")
    
    elif 'ERROR500' in customer_id.upper():
        # Simulate 500 error (bank service unavailable)
        raise Exception("Bank validation service temporarily unavailable on September 4th 7.06 AM")
    
    elif 'SLOW' in customer_id.upper():
        # Simulate slow processing
        time.sleep(3.0)
    
    # Happy path - successful validation
    return {
        'validation_id': f"VAL-{int(time.time())}-{random.randint(1000, 9999)}",
        'status': 'validated',
        'routing_number': routing_number,
        'account_number_masked': f"****{account_number[-4:]}",
        'bank_name': f"Bank of {routing_number[:3]}",
        'account_type': 'checking',
        'validation_timestamp': datetime.utcnow().isoformat(),
        'processing_time_seconds': processing_time
    }

def process_bank_account_message(message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single bank account setup message"""
    
    message_id = message_body.get('message_id', f"msg-{int(time.time())}")
    customer_id = message_body.get('customer_id', 'unknown')
    message_group_id = message_body.get('message_group_id', customer_id)
    
    start_time = time.time()
        
    try:
        logger.info(f"Processing bank account setup for customer on September 4th at 6.40 AM: {customer_id}")
        
        # Validate required fields
        required_fields = ['customer_id', 'routing_number', 'account_number']
        for field in required_fields:
            if not message_body.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Simulate bank account validation
        validation_result = simulate_bank_account_validation(message_body)
        
        # Record successful processing
        processing_time = time.time() - start_time
        
        logger.info(f"Successfully processed bank account setup: {validation_result['validation_id']}")
        
        return {
            'status': 'success',
            'message_id': message_id,
            'customer_id': customer_id,
            'validation_result': validation_result,
            'processing_time': processing_time
        }
        
    except Exception as e:
        # Handle error using error handler
        processing_time = time.time() - start_time
        
        # Determine status code based on error message
        status_code = None
        if 'invalid' in str(e).lower() or 'format' in str(e).lower():
            status_code = 400
        elif 'unavailable' in str(e).lower() or 'service' in str(e).lower():
            status_code = 500
        
        error_result = error_handler.handle_error(e, message_body, status_code)
        
        logger.error(f"Error processing bank account setup: {e}")
        
        return {
            'status': 'error',
            'message_id': message_id,
            'customer_id': customer_id,
            'error': str(e),
            'error_info': error_result['error_info'],
            'action': error_result['action'],
            'processing_time': processing_time
        }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for bank account setup processing
    Simplified - only handles SQS messages (business logic only)
    """
    
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    try:
        # Handle SQS messages (bank account setup requests)
        if 'Records' in event:
            results = []
            
            for record in event['Records']:
                if record.get('eventSource') == 'aws:sqs':
                    # Parse SQS message
                    message_body = json.loads(record['body'])
                    
                    # If message came through SNS->SQS, extract the actual message
                    if 'Message' in message_body:
                        message_body = json.loads(message_body['Message'])
                    
                    # Process the message
                    result = process_bank_account_message(message_body)
                    results.append(result)
            
            successful = len([r for r in results if r['status'] == 'success'])
            failed = len([r for r in results if r['status'] == 'error'])
            
            logger.info(f"Processed {len(results)} messages: {successful} successful, {failed} failed")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'processed': len(results),
                    'successful': successful,
                    'failed': failed,
                    'results': results
                })
            }
            
        else:
            # Direct invocation or test
            logger.info("Direct invocation - processing single message")
            result = process_bank_account_message(event)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Internal server error'
            })
        }