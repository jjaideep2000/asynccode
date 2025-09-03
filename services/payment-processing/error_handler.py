"""
Error handling utilities for utility customer system
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types of errors that can occur"""
    CLIENT_ERROR = "client_error"  # 4xx errors
    SERVER_ERROR = "server_error"  # 5xx errors
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"

class SubscriptionManager:
    """Manages Lambda subscription to SQS queues"""
    
    def __init__(self, function_name: str, event_source_mapping_uuid: str = None):
        self.function_name = function_name
        self.event_source_mapping_uuid = event_source_mapping_uuid
        self.lambda_client = boto3.client('lambda')
        self.sns_client = boto3.client('sns')
        
        # If UUID not provided, try to discover it
        if not self.event_source_mapping_uuid:
            self.event_source_mapping_uuid = self._discover_event_source_mapping_uuid()
    
    def _discover_event_source_mapping_uuid(self) -> str:
        """Discover the event source mapping UUID for this function"""
        try:
            logger.info(f"Discovering event source mapping UUID for function: {self.function_name}")
            response = self.lambda_client.list_event_source_mappings(FunctionName=self.function_name)
            
            logger.info(f"Found {len(response['EventSourceMappings'])} event source mappings")
            
            # Find SQS event source mapping
            for mapping in response['EventSourceMappings']:
                event_source_arn = mapping.get('EventSourceArn', '')
                logger.info(f"Checking mapping: {mapping['UUID']} -> {event_source_arn}")
                
                if 'sqs' in event_source_arn.lower():
                    logger.info(f"✅ Discovered SQS event source mapping UUID: {mapping['UUID']}")
                    return mapping['UUID']
            
            logger.warning(f"❌ No SQS event source mapping found for {self.function_name}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to discover event source mapping UUID: {e}")
            return None
    
    def disable_subscription(self) -> bool:
        """Disable SQS event source mapping"""
        if not self.event_source_mapping_uuid:
            logger.error("❌ No event source mapping UUID available - cannot disable subscription")
            return False
            
        try:
            response = self.lambda_client.update_event_source_mapping(
                UUID=self.event_source_mapping_uuid,
                Enabled=False
            )
            logger.warning(f"🚨 DISABLED subscription for {self.function_name} (UUID: {self.event_source_mapping_uuid})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to disable subscription: {e}")
            return False
    
    def enable_subscription(self) -> bool:
        """Enable SQS event source mapping"""
        if not self.event_source_mapping_uuid:
            logger.error("❌ No event source mapping UUID available - cannot enable subscription")
            return False
            
        try:
            response = self.lambda_client.update_event_source_mapping(
                UUID=self.event_source_mapping_uuid,
                Enabled=True
            )
            logger.info(f"✅ ENABLED subscription for {self.function_name} (UUID: {self.event_source_mapping_uuid})")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to enable subscription: {e}")
            return False
    
    def get_subscription_status(self) -> bool:
        """Check if subscription is enabled"""
        if not self.event_source_mapping_uuid:
            logger.warning("❌ No event source mapping UUID available - cannot check status")
            return False
            
        try:
            response = self.lambda_client.get_event_source_mapping(
                UUID=self.event_source_mapping_uuid
            )
            status = response.get('State') == 'Enabled'
            logger.info(f"📊 Subscription status for {self.function_name}: {'Enabled' if status else 'Disabled'}")
            return status
        except Exception as e:
            logger.error(f"❌ Failed to get subscription status: {e}")
            return False

class ErrorHandler:
    """Handles different types of errors and implements retry logic"""
    
    def __init__(self, service_name: str, subscription_manager: SubscriptionManager = None):
        self.service_name = service_name
        self.subscription_manager = subscription_manager
    
    def classify_error(self, error: Exception, status_code: Optional[int] = None) -> ErrorType:
        """Classify error type based on exception and status code"""
        
        if status_code:
            if 400 <= status_code < 500:
                return ErrorType.CLIENT_ERROR
            elif 500 <= status_code < 600:
                return ErrorType.SERVER_ERROR
        
        # Classify by exception type
        error_name = type(error).__name__
        
        if error_name in ['ConnectionError', 'TimeoutError', 'ConnectTimeout']:
            return ErrorType.NETWORK_ERROR
        elif error_name in ['ValueError', 'ValidationError', 'KeyError']:
            return ErrorType.VALIDATION_ERROR
        else:
            return ErrorType.PROCESSING_ERROR
    
    def should_retry(self, error_type: ErrorType) -> bool:
        """Determine if error should be retried"""
        
        # Retry network errors and server errors
        if error_type in [ErrorType.NETWORK_ERROR, ErrorType.SERVER_ERROR]:
            return True
        
        # Don't retry client errors or validation errors
        return False
    
    def should_stop_subscription(self, error_type: ErrorType) -> bool:
        """Determine if subscription should be stopped"""
        
        # Stop subscription for server errors (5xx)
        return error_type == ErrorType.SERVER_ERROR
    
    def handle_error(self, error: Exception, message_data: Dict[str, Any], 
                    status_code: Optional[int] = None) -> Dict[str, Any]:
        """
        Handle error according to business rules:
        - 400 errors: Continue processing
        - 500 errors: Stop subscription
        - Other errors: Log and continue
        """
        
        error_type = self.classify_error(error, status_code)
        
        error_info = {
            'error_type': error_type.value,
            'error_message': str(error),
            'status_code': status_code,
            'service': self.service_name,
            'message_id': message_data.get('message_id', 'unknown'),
            'customer_id': message_data.get('customer_id', 'unknown')
        }
        
        logger.error(f"Error processing message: {error_info}")
        
        # Handle based on error type
        if error_type == ErrorType.CLIENT_ERROR:
            # 400 errors - continue processing
            logger.info("Client error (4xx) - continuing processing")
            return {
                'action': 'continue',
                'retry': False,
                'error_info': error_info
            }
        
        elif error_type == ErrorType.SERVER_ERROR:
            # 500 errors - stop subscription
            logger.warning("Server error (5xx) - stopping subscription")
            
            if self.subscription_manager:
                success = self.subscription_manager.disable_subscription()
                error_info['subscription_disabled'] = success
            
            return {
                'action': 'stop_subscription',
                'retry': False,
                'error_info': error_info
            }
        
        else:
            # Other errors - log and continue
            logger.info(f"Other error ({error_type.value}) - continuing processing")
            return {
                'action': 'continue',
                'retry': self.should_retry(error_type),
                'error_info': error_info
            }
    
    def handle_subscription_control_message(self, message: Dict[str, Any]) -> bool:
        """Handle subscription control messages from SNS"""
        
        try:
            # Parse SNS message
            if 'Records' in message:
                # Lambda SNS event format
                sns_message = json.loads(message['Records'][0]['Sns']['Message'])
            else:
                # Direct message format
                sns_message = message
            
            action = sns_message.get('action', '').lower()
            target_service = sns_message.get('service', '').lower()
            
            # Check if message is for this service
            if target_service and target_service != self.service_name.lower():
                logger.info(f"Subscription control message not for this service: {target_service}")
                return True
            
            if not self.subscription_manager:
                logger.warning("No subscription manager configured")
                return False
            
            # Handle actions
            if action == 'start' or action == 'enable':
                logger.info("Received start subscription command")
                return self.subscription_manager.enable_subscription()
            
            elif action == 'stop' or action == 'disable':
                logger.info("Received stop subscription command")
                return self.subscription_manager.disable_subscription()
            
            else:
                logger.warning(f"Unknown subscription control action: {action}")
                return False
        
        except Exception as e:
            logger.error(f"Error handling subscription control message: {e}")
            return False

def create_error_handler(service_name: str, event_source_mapping_uuid: str = None) -> ErrorHandler:
    """Create error handler with subscription manager that discovers UUID dynamically"""
    
    # Always create subscription manager - it will discover UUID at runtime
    function_name = f"utility-customer-system-dev-{service_name}"
    subscription_manager = SubscriptionManager(function_name, event_source_mapping_uuid)
    
    return ErrorHandler(service_name, subscription_manager)