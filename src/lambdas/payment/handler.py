"""
Payment Processing Lambda Handler
Processes utility bill payment requests from customers
"""

import json
import os
import time
import random
import logging
from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

# Import shared utilities
import sys
sys.path.append('/opt/python')  # Lambda layer path
sys.path.append('../../shared')  # Local development path

try:
    from shared.error_handler import create_error_handler
except ImportError:
    # Fallback for when shared is in the same directory
    from error_handler import create_error_handler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_NAME = "payment-processing"

# Initialize error handler with dynamic UUID discovery
# The error handler will automatically discover the event source mapping UUID at runtime
error_handler = create_error_handler(SERVICE_NAME)

def simulate_payment_processing(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate payment processing
    Returns processing result with potential errors for testing
    """
    
    customer_id = payment_data.get('customer_id', 'unknown')
    amount = float(payment_data.get('amount', 0))
    payment_method = payment_data.get('payment_method', 'bank_account')
    
    # Simulate processing time based on amount
    base_time = 0.5
    amount_factor = min(amount / 1000, 2.0)  # Larger amounts take longer
    processing_time = random.uniform(base_time, base_time + amount_factor)
    time.sleep(processing_time)
    
    # Simulate different scenarios based on customer ID or amount
    if 'ERROR400' in customer_id.upper():
        # Simulate 400 error (insufficient funds)
        raise Exception("Insufficient funds in account")
    
    elif 'ERROR500' in customer_id.upper():
        # Simulate 500 error (payment gateway unavailable)
        raise Exception("Payment gateway temporarily unavailable")
    
    elif amount > 10000:
        # Simulate large payment requiring additional verification
        time.sleep(2.0)
        processing_time += 2.0
    
    elif amount <= 0:
        # Invalid amount
        raise ValueError("Payment amount must be greater than zero")
    
    # Happy path - successful payment
    transaction_id = f"TXN-{int(time.time())}-{random.randint(10000, 99999)}"
    
    return {
        'transaction_id': transaction_id,
        'status': 'completed',
        'amount': amount,
        'currency': 'USD',
        'payment_method': payment_method,
        'confirmation_number': f"CONF-{random.randint(100000, 999999)}",
        'processed_timestamp': datetime.utcnow().isoformat(),
        'processing_time_seconds': processing_time,
        'fees': round(amount * 0.025, 2) if amount > 100 else 0,  # 2.5% fee for large payments
        'net_amount': amount - (round(amount * 0.025, 2) if amount > 100 else 0)
    }

def process_payment_message(message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single payment message"""
    
    message_id = message_body.get('message_id', f"msg-{int(time.time())}")
    customer_id = message_body.get('customer_id', 'unknown')
    message_group_id = message_body.get('message_group_id', customer_id)
    amount = message_body.get('amount', 0)
    
    start_time = time.time()
        
    try:
        logger.info(f"Processing payment for customer: {customer_id}, amount: ${amount}")
        
        # Validate required fields
        required_fields = ['customer_id', 'amount', 'payment_method']
        for field in required_fields:
            if not message_body.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Validate amount
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValueError("Amount must be greater than zero")
        except (ValueError, TypeError):
            raise ValueError("Invalid amount format")
        
        # Simulate payment processing
        payment_result = simulate_payment_processing(message_body)
        
        # Record successful processing
        processing_time = time.time() - start_time
        
        logger.info(f"Successfully processed payment: {payment_result['transaction_id']}")
        
        return {
            'status': 'success',
            'message_id': message_id,
            'customer_id': customer_id,
            'payment_result': payment_result,
            'processing_time': processing_time
        }
        
    except Exception as e:
        # Handle error using error handler
        processing_time = time.time() - start_time
        
        # Determine status code based on error message
        status_code = None
        error_msg = str(e).lower()
        
        if any(word in error_msg for word in ['insufficient', 'invalid', 'missing', 'format']):
            status_code = 400
        elif any(word in error_msg for word in ['unavailable', 'gateway', 'service']):
            status_code = 500
        
        error_result = error_handler.handle_error(e, message_body, status_code)
        
        logger.error(f"Error processing payment: {e}")
        
        return {
            'status': 'error',
            'message_id': message_id,
            'customer_id': customer_id,
            'amount': amount,
            'error': str(e),
            'error_info': error_result['error_info'],
            'action': error_result['action'],
            'processing_time': processing_time
        }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for payment processing
    Simplified - only handles SQS messages (business logic only)
    """
    
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    try:
        # Handle SQS messages (payment requests)
        if 'Records' in event:
            results = []
            total_amount = 0
            
            for record in event['Records']:
                if record.get('eventSource') == 'aws:sqs':
                    # Parse SQS message
                    message_body = json.loads(record['body'])
                    
                    # If message came through SNS->SQS, extract the actual message
                    if 'Message' in message_body:
                        message_body = json.loads(message_body['Message'])
                    
                    # Process the message
                    result = process_payment_message(message_body)
                    results.append(result)
                    
                    # Track total amount processed
                    if result['status'] == 'success':
                        total_amount += result['payment_result']['amount']
            
            successful = len([r for r in results if r['status'] == 'success'])
            failed = len([r for r in results if r['status'] == 'error'])
            
            logger.info(f"Processed {len(results)} payments: {successful} successful (${total_amount:.2f}), {failed} failed")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'processed': len(results),
                    'successful': successful,
                    'failed': failed,
                    'total_amount': total_amount,
                    'results': results
                })
            }
            
        else:
            # Direct invocation or test
            logger.info("Direct invocation - processing single payment")
            result = process_payment_message(event)
            
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