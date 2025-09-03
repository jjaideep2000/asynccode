#!/usr/bin/env python3
"""
Simple Lambda function test to diagnose execution issues
"""

import json
import boto3
import time

def test_lambda_direct():
    """Test Lambda functions directly"""
    
    print("DIRECT LAMBDA FUNCTION TEST")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda')
    
    # Test bank account setup function
    print("\nTesting Bank Account Setup Function")
    print("-" * 40)
    
    try:
        test_payload = {
            'customer_id': 'test-customer-001',
            'routing_number': '123456789',
            'account_number': '987654321',
            'message_id': 'direct-test-msg'
        }
        
        response = lambda_client.invoke(
            FunctionName='utility-customer-system-dev-bank-account-setup',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Status Code: {response['StatusCode']}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Test observability function
    print("\nTesting Observability Function")
    print("-" * 40)
    
    try:
        obs_payload = {
            'customer_id': 'obs-test-customer',
            'event_type': 'CUSTOMER_EVENT',
            'message': 'Direct test of observability function'
        }
        
        response = lambda_client.invoke(
            FunctionName='utility-customer-system-dev-bank-account-observability',
            InvocationType='RequestResponse',
            Payload=json.dumps(obs_payload)
        )
        
        result = json.loads(response['Payload'].read())
        print(f"Status Code: {response['StatusCode']}")
        print(f"Response: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")

def check_lambda_configuration():
    """Check Lambda function configuration"""
    
    print("\nLAMBDA CONFIGURATION CHECK")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda')
    
    functions = [
        'utility-customer-system-dev-bank-account-setup',
        'utility-customer-system-dev-payment-processing',
        'utility-customer-system-dev-bank-account-observability'
    ]
    
    for func_name in functions:
        print(f"\n{func_name}")
        print("-" * 30)
        
        try:
            config = lambda_client.get_function_configuration(FunctionName=func_name)
            
            print(f"Runtime: {config['Runtime']}")
            print(f"Handler: {config['Handler']}")
            print(f"Timeout: {config['Timeout']} seconds")
            print(f"Memory: {config['MemorySize']} MB")
            print(f"Last Modified: {config['LastModified']}")
            
            if 'Environment' in config and 'Variables' in config['Environment']:
                env_vars = config['Environment']['Variables']
                print(f"Environment Variables: {list(env_vars.keys())}")
            
        except Exception as e:
            print(f"Error getting config: {e}")

if __name__ == "__main__":
    print("Simple Lambda Function Test")
    
    # Check configuration first
    check_lambda_configuration()
    
    # Test functions directly
    test_lambda_direct()
    
    print("\nTest complete!")