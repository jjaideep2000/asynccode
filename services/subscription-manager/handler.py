#!/usr/bin/env python3
"""
Subscription Manager Lambda Handler
Centralized subscription control for all Lambda functions in the system
Receives SNS messages and manages event source mappings for multiple Lambdas
"""

import json
import os
import time
import logging
from typing import Dict, Any, List
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICE_NAME = "subscription-manager"

class SubscriptionManager:
    """Centralized subscription management for Lambda functions"""
    
    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.sns_client = boto3.client('sns')
        
        # Configuration for managed Lambda functions
        self.managed_functions = self._load_managed_functions()
        
    def _load_managed_functions(self) -> List[Dict[str, str]]:
        """Load configuration of Lambda functions to manage"""
        
        # This could be loaded from environment variables, SSM Parameter Store, or DynamoDB
        # For now, we'll use environment variables with fallback to defaults
        
        functions_config = os.getenv('MANAGED_FUNCTIONS', '')
        
        if functions_config:
            try:
                return json.loads(functions_config)
            except json.JSONDecodeError:
                logger.error("Invalid MANAGED_FUNCTIONS configuration")
        
        # Default configuration - these are the current Lambda functions
        return [
            {
                "function_name": "utility-customer-system-dev-bank-account-setup",
                "service_name": "bank-account-setup",
                "description": "Bank account setup processing"
            },
            {
                "function_name": "utility-customer-system-dev-payment-processing", 
                "service_name": "payment-processing",
                "description": "Payment processing"
            }
            # Future Lambda functions can be added here
        ]
    
    def handle_subscription_control(self, control_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle subscription control message for all managed Lambda functions
        
        Args:
            control_message: SNS message with action (enable/disable)
            
        Returns:
            Results of subscription operations
        """
        
        action = control_message.get('action', '').lower()
        reason = control_message.get('reason', 'Manual control')
        operator = control_message.get('operator', 'system')
        timestamp = control_message.get('timestamp', datetime.utcnow().isoformat())
        
        logger.info(f"Processing subscription control: action={action}, reason={reason}")
        
        if action not in ['enable', 'disable']:
            raise ValueError(f"Invalid action: {action}. Must be 'enable' or 'disable'")
        
        results = {
            'action': action,
            'timestamp': timestamp,
            'operator': operator,
            'reason': reason,
            'functions_processed': [],
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }
        
        # Process each managed Lambda function
        for function_config in self.managed_functions:
            function_name = function_config['function_name']
            service_name = function_config['service_name']
            
            try:
                logger.info(f"Processing {service_name} ({function_name})")
                
                if action == 'enable':
                    function_result = self._enable_function_subscriptions(function_config)
                else:  # disable
                    function_result = self._disable_function_subscriptions(function_config)
                
                function_result['function_name'] = function_name
                function_result['service_name'] = service_name
                results['functions_processed'].append(function_result)
                
                if function_result['success']:
                    results['success_count'] += 1
                    logger.info(f"✅ {service_name}: {action} successful")
                else:
                    results['error_count'] += 1
                    logger.error(f" {service_name}: {action} failed")
                    
            except Exception as e:
                error_msg = f"Error processing {service_name}: {str(e)}"
                logger.error(error_msg)
                
                results['functions_processed'].append({
                    'function_name': function_name,
                    'service_name': service_name,
                    'success': False,
                    'error': error_msg,
                    'mappings_processed': 0
                })
                results['error_count'] += 1
                results['errors'].append(error_msg)
        
        # Log summary
        logger.info(f"Subscription control complete: {results['success_count']} success, {results['error_count']} errors")
        
        return results
    
    def _enable_function_subscriptions(self, function_config: Dict[str, str]) -> Dict[str, Any]:
        """Enable all SQS event source mappings for a Lambda function"""
        
        function_name = function_config['function_name']
        result = {
            'success': True,
            'mappings_processed': 0,
            'mappings_enabled': 0,
            'mappings_already_enabled': 0,
            'errors': []
        }
        
        try:
            # Get all event source mappings for this function
            response = self.lambda_client.list_event_source_mappings(
                FunctionName=function_name
            )
            
            sqs_mappings = [
                mapping for mapping in response['EventSourceMappings']
                if 'sqs' in mapping['EventSourceArn'].lower()
            ]
            
            result['mappings_processed'] = len(sqs_mappings)
            
            for mapping in sqs_mappings:
                uuid = mapping['UUID']
                current_state = mapping['State']
                event_source_arn = mapping['EventSourceArn']
                
                logger.info(f"Processing mapping {uuid}: current state = {current_state}")
                
                if current_state == 'Disabled':
                    try:
                        # Enable the mapping
                        self.lambda_client.update_event_source_mapping(
                            UUID=uuid,
                            Enabled=True
                        )
                        
                        result['mappings_enabled'] += 1
                        logger.info(f"✅ Enabled mapping {uuid} for {function_name}")
                        
                    except ClientError as e:
                        error_msg = f"Failed to enable mapping {uuid}: {str(e)}"
                        result['errors'].append(error_msg)
                        logger.error(error_msg)
                        
                elif current_state == 'Enabled':
                    result['mappings_already_enabled'] += 1
                    logger.info(f"ℹ️  Mapping {uuid} already enabled")
                    
                else:
                    logger.warning(f"⚠️  Mapping {uuid} in unexpected state: {current_state}")
            
            # Check if any mappings failed
            if result['errors']:
                result['success'] = False
                
        except Exception as e:
            result['success'] = False
            result['errors'].append(f"Failed to list event source mappings: {str(e)}")
            
        return result
    
    def _disable_function_subscriptions(self, function_config: Dict[str, str]) -> Dict[str, Any]:
        """Disable all SQS event source mappings for a Lambda function"""
        
        function_name = function_config['function_name']
        result = {
            'success': True,
            'mappings_processed': 0,
            'mappings_disabled': 0,
            'mappings_already_disabled': 0,
            'errors': []
        }
        
        try:
            # Get all event source mappings for this function
            response = self.lambda_client.list_event_source_mappings(
                FunctionName=function_name
            )
            
            sqs_mappings = [
                mapping for mapping in response['EventSourceMappings']
                if 'sqs' in mapping['EventSourceArn'].lower()
            ]
            
            result['mappings_processed'] = len(sqs_mappings)
            
            for mapping in sqs_mappings:
                uuid = mapping['UUID']
                current_state = mapping['State']
                event_source_arn = mapping['EventSourceArn']
                
                logger.info(f"Processing mapping {uuid}: current state = {current_state}")
                
                if current_state == 'Enabled':
                    try:
                        # Disable the mapping
                        self.lambda_client.update_event_source_mapping(
                            UUID=uuid,
                            Enabled=False
                        )
                        
                        result['mappings_disabled'] += 1
                        logger.info(f" Disabled mapping {uuid} for {function_name}")
                        
                    except ClientError as e:
                        error_msg = f"Failed to disable mapping {uuid}: {str(e)}"
                        result['errors'].append(error_msg)
                        logger.error(error_msg)
                        
                elif current_state == 'Disabled':
                    result['mappings_already_disabled'] += 1
                    logger.info(f" Mapping {uuid} already disabled")
                    
                else:
                    logger.warning(f"  Mapping {uuid} in unexpected state: {current_state}")
            
            # Check if any mappings failed
            if result['errors']:
                result['success'] = False
                
        except Exception as e:
            result['success'] = False
            result['errors'].append(f"Failed to list event source mappings: {str(e)}")
            
        return result
    
    def get_subscription_status(self) -> Dict[str, Any]:
        """Get current subscription status for all managed functions"""
        
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'functions': [],
            'summary': {
                'total_functions': len(self.managed_functions),
                'enabled_functions': 0,
                'disabled_functions': 0,
                'mixed_state_functions': 0,
                'error_functions': 0
            }
        }
        
        for function_config in self.managed_functions:
            function_name = function_config['function_name']
            service_name = function_config['service_name']
            
            try:
                # Get event source mappings
                response = self.lambda_client.list_event_source_mappings(
                    FunctionName=function_name
                )
                
                sqs_mappings = [
                    mapping for mapping in response['EventSourceMappings']
                    if 'sqs' in mapping['EventSourceArn'].lower()
                ]
                
                enabled_count = sum(1 for m in sqs_mappings if m['State'] == 'Enabled')
                disabled_count = sum(1 for m in sqs_mappings if m['State'] == 'Disabled')
                total_count = len(sqs_mappings)
                
                # Determine overall status
                if total_count == 0:
                    overall_status = 'no_mappings'
                elif enabled_count == total_count:
                    overall_status = 'enabled'
                    status['summary']['enabled_functions'] += 1
                elif disabled_count == total_count:
                    overall_status = 'disabled'
                    status['summary']['disabled_functions'] += 1
                else:
                    overall_status = 'mixed'
                    status['summary']['mixed_state_functions'] += 1
                
                function_status = {
                    'function_name': function_name,
                    'service_name': service_name,
                    'overall_status': overall_status,
                    'total_mappings': total_count,
                    'enabled_mappings': enabled_count,
                    'disabled_mappings': disabled_count,
                    'mappings': [
                        {
                            'uuid': m['UUID'],
                            'state': m['State'],
                            'event_source_arn': m['EventSourceArn']
                        }
                        for m in sqs_mappings
                    ]
                }
                
                status['functions'].append(function_status)
                
            except Exception as e:
                logger.error(f"Error getting status for {function_name}: {e}")
                
                status['functions'].append({
                    'function_name': function_name,
                    'service_name': service_name,
                    'overall_status': 'error',
                    'error': str(e)
                })
                status['summary']['error_functions'] += 1
        
        return status


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for subscription management
    Handles SNS messages for subscription control
    """
    
    logger.info(f"Receivedddddddddddddd event: {json.dumps(event, default=str)}")
    
    try:
        subscription_manager = SubscriptionManager()
        
        # Handle SNS messages
        if 'Records' in event:
            results = []
            
            for record in event['Records']:
                if record.get('EventSource') == 'aws:sns':
                    # Extract SNS message
                    sns_record = record['Sns']
                    message_body = json.loads(sns_record['Message'])
                    
                    logger.info(f"Processing SNS message: {message_body}")
                    
                    # Handle subscription control
                    result = subscription_manager.handle_subscription_control(message_body)
                    results.append(result)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Subscription control processed',
                    'results': results
                })
            }
        
        # Handle direct invocation (for testing or status checks)
        elif event.get('action') == 'status':
            status = subscription_manager.get_subscription_status()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Subscription status retrieved',
                    'status': status
                })
            }
        
        # Handle direct subscription control
        elif event.get('action') in ['enable', 'disable']:
            result = subscription_manager.handle_subscription_control(event)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Subscription {event["action"]} processed',
                    'result': result
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid event format or missing action'
                })
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


# For testing
if __name__ == "__main__":
    # Test the subscription manager
    manager = SubscriptionManager()
    
    # Get current status
    status = manager.get_subscription_status()
    print("Current Status:")
    print(json.dumps(status, indent=2))
    
    # Test enable action
    test_message = {
        'action': 'enable',
        'reason': 'Testing centralized subscription management',
        'operator': 'test_user'
    }
    
    result = manager.handle_subscription_control(test_message)
    print("\nEnable Result:")
    print(json.dumps(result, indent=2))