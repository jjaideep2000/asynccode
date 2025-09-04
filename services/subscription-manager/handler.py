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
        self._last_config_refresh = time.time()
        self._config_refresh_interval = int(os.getenv('CONFIG_REFRESH_INTERVAL', '300'))  # 5 minutes default
        
    def _load_managed_functions(self) -> List[Dict[str, str]]:
        """Load configuration of Lambda functions to manage dynamically - NO HARDCODING"""
        
        # Try multiple dynamic sources in order of preference
        
        # 1. Try auto-discovery by AWS Lambda API (fully dynamic - primary method)
        functions = self._auto_discover_all_functions()
        if functions:
            logger.info(f"Auto-discovered {len(functions)} functions by AWS API scan")
            return functions
        
        # 2. Try SSM Parameter Store (manual override)
        functions = self._load_from_ssm()
        if functions:
            logger.info(f"Loaded {len(functions)} functions from SSM Parameter Store")
            return functions
        
        # 3. Try DynamoDB table (complex configurations)
        functions = self._load_from_dynamodb()
        if functions:
            logger.info(f"Loaded {len(functions)} functions from DynamoDB")
            return functions
        
        # 4. Try auto-discovery by tags (tagged functions only)
        functions = self._auto_discover_functions()
        if functions:
            logger.info(f"Auto-discovered {len(functions)} functions by tags")
            return functions
        
        # 5. Try environment variable (simple override)
        functions_config = os.getenv('MANAGED_FUNCTIONS', '')
        if functions_config:
            try:
                functions = json.loads(functions_config)
                logger.info(f"Loaded {len(functions)} functions from environment variable")
                return functions
            except json.JSONDecodeError:
                logger.error("Invalid MANAGED_FUNCTIONS configuration")
        
        # 6. NO HARDCODED FALLBACK - Return empty list if nothing found
        logger.error("No Lambda functions found through any discovery method!")
        logger.error("Available methods: AWS API scan, SSM, DynamoDB, tags, environment")
        return []
    
    def _load_from_ssm(self) -> List[Dict[str, str]]:
        """Load function configuration from SSM Parameter Store"""
        try:
            ssm_client = boto3.client('ssm')
            parameter_name = os.getenv('SSM_FUNCTIONS_PARAMETER', '/utility-system/subscription-manager/managed-functions')
            
            response = ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )
            
            return json.loads(response['Parameter']['Value'])
            
        except Exception as e:
            logger.debug(f"Could not load from SSM: {e}")
            return []
    
    def _load_from_dynamodb(self) -> List[Dict[str, str]]:
        """Load function configuration from DynamoDB table"""
        try:
            dynamodb = boto3.resource('dynamodb')
            table_name = os.getenv('DYNAMODB_FUNCTIONS_TABLE', 'utility-system-managed-functions')
            table = dynamodb.Table(table_name)
            
            response = table.scan()
            
            # Convert DynamoDB items to function config format
            functions = []
            for item in response['Items']:
                functions.append({
                    'function_name': item['function_name'],
                    'service_name': item['service_name'],
                    'description': item.get('description', ''),
                    'enabled': item.get('enabled', True)
                })
            
            # Only return enabled functions
            return [f for f in functions if f.get('enabled', True)]
            
        except Exception as e:
            logger.debug(f"Could not load from DynamoDB: {e}")
            return []
    
    def _auto_discover_all_functions(self) -> List[Dict[str, str]]:
        """Auto-discover ALL Lambda functions by scanning AWS and matching naming pattern"""
        try:
            # Configuration
            function_prefix = os.getenv('FUNCTION_PREFIX', 'utility-customer-system-dev-')
            exclude_functions = os.getenv('EXCLUDE_FUNCTIONS', 'subscription-manager').split(',')
            
            logger.info(f"Scanning for Lambda functions with prefix: {function_prefix}")
            
            # List all Lambda functions with pagination
            functions = []
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    function_name = function['FunctionName']
                    
                    # Skip if doesn't match our naming pattern
                    if not function_name.startswith(function_prefix):
                        logger.debug(f"Skipping {function_name} - doesn't match prefix {function_prefix}")
                        continue
                    
                    # Extract service name from function name
                    service_name = function_name.replace(function_prefix, '')
                    
                    # Skip excluded functions (like subscription-manager itself)
                    if any(exclude in service_name for exclude in exclude_functions):
                        logger.debug(f"Skipping {function_name} - in exclude list")
                        continue
                    
                    # Check if function has SQS event source mappings (processing functions)
                    try:
                        mappings_response = self.lambda_client.list_event_source_mappings(
                            FunctionName=function_name
                        )
                        
                        sqs_mappings = [
                            mapping for mapping in mappings_response['EventSourceMappings']
                            if 'sqs' in mapping['EventSourceArn'].lower()
                        ]
                        
                        # Only include functions that have SQS mappings (processing functions)
                        if sqs_mappings:
                            functions.append({
                                'function_name': function_name,
                                'service_name': service_name,
                                'description': f'Auto-discovered processing service: {service_name}',
                                'sqs_mappings_count': len(sqs_mappings),
                                'auto_discovered': True,
                                'discovery_method': 'aws_api_scan'
                            })
                            
                            logger.info(f"✅ Discovered processing function: {service_name} ({len(sqs_mappings)} SQS mappings)")
                        else:
                            logger.debug(f"Skipping {function_name} - no SQS event source mappings")
                            
                    except Exception as e:
                        logger.debug(f"Could not check event source mappings for {function_name}: {e}")
                        continue
            
            logger.info(f"Auto-discovery complete: found {len(functions)} processing functions")
            return functions
            
        except Exception as e:
            logger.error(f"Auto-discovery failed: {e}")
            return []

    def _auto_discover_functions(self) -> List[Dict[str, str]]:
        """Auto-discover Lambda functions by tags"""
        try:
            # Look for Lambda functions with specific tags
            tag_key = os.getenv('DISCOVERY_TAG_KEY', 'SubscriptionManaged')
            tag_value = os.getenv('DISCOVERY_TAG_VALUE', 'true')
            function_prefix = os.getenv('FUNCTION_PREFIX', 'utility-customer-system-dev-')
            
            # List all Lambda functions with pagination
            functions = []
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    function_name = function['FunctionName']
                    
                    # Skip if doesn't match prefix
                    if not function_name.startswith(function_prefix):
                        continue
                    
                    # Skip subscription-manager itself
                    if 'subscription-manager' in function_name:
                        continue
                    
                    try:
                        # Check function tags
                        tags_response = self.lambda_client.list_tags(
                            Resource=function['FunctionArn']
                        )
                        
                        tags = tags_response.get('Tags', {})
                        
                        # Check if function should be managed
                        if tags.get(tag_key) == tag_value:
                            # Extract service name from function name
                            service_name = function_name.replace(function_prefix, '')
                            
                            functions.append({
                                'function_name': function_name,
                                'service_name': service_name,
                                'description': tags.get('Description', f'Auto-discovered {service_name}'),
                                'auto_discovered': True
                            })
                            
                    except Exception as e:
                        logger.debug(f"Could not check tags for {function_name}: {e}")
                        continue
            
            return functions
            
        except Exception as e:
            logger.debug(f"Auto-discovery failed: {e}")
            return []
    
    # NO HARDCODED FUNCTIONS - All discovery is dynamic!
    
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
        
        # Auto-refresh configuration if needed
        self.refresh_configuration()
        
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
    
    def refresh_configuration(self, force: bool = False) -> Dict[str, Any]:
        """Refresh the managed functions configuration"""
        
        current_time = time.time()
        time_since_refresh = current_time - self._last_config_refresh
        
        if not force and time_since_refresh < self._config_refresh_interval:
            return {
                'refreshed': False,
                'reason': f'Last refresh was {time_since_refresh:.1f} seconds ago (interval: {self._config_refresh_interval}s)',
                'functions_count': len(self.managed_functions)
            }
        
        old_functions = self.managed_functions.copy()
        self.managed_functions = self._load_managed_functions()
        self._last_config_refresh = current_time
        
        # Compare configurations
        old_names = {f['function_name'] for f in old_functions}
        new_names = {f['function_name'] for f in self.managed_functions}
        
        added = new_names - old_names
        removed = old_names - new_names
        
        logger.info(f"Configuration refreshed: {len(self.managed_functions)} functions loaded")
        if added:
            logger.info(f"Added functions: {list(added)}")
        if removed:
            logger.info(f"Removed functions: {list(removed)}")
        
        return {
            'refreshed': True,
            'timestamp': datetime.utcnow().isoformat(),
            'old_count': len(old_functions),
            'new_count': len(self.managed_functions),
            'added_functions': list(added),
            'removed_functions': list(removed),
            'current_functions': [f['function_name'] for f in self.managed_functions]
        }


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
        
        # Handle configuration refresh
        elif event.get('action') == 'refresh':
            force_refresh = event.get('force', False)
            refresh_result = subscription_manager.refresh_configuration(force=force_refresh)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Configuration refresh processed',
                    'result': refresh_result
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