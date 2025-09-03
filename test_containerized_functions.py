#!/usr/bin/env python3
"""
Test script for containerized Lambda functions
"""

import boto3
import json
import time
from datetime import datetime

def test_containerized_lambdas():
    """Test all containerized Lambda functions"""
    
    # Initialize Lambda client
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    # Test configurations
    tests = [
        {
            'function_name': 'utility-customer-system-dev-bank-account-setup',
            'payload': {
                'customer_id': 'test123',
                'routing_number': '123456789',
                'account_number': '987654321'
            },
            'description': 'Bank Account Setup'
        },
        {
            'function_name': 'utility-customer-system-dev-payment-processing',
            'payload': {
                'customer_id': 'test123',
                'amount': 100.50,
                'payment_method': 'bank_transfer'
            },
            'description': 'Payment Processing'
        },
        {
            'function_name': 'utility-customer-system-dev-subscription-manager',
            'payload': {
                'action': 'status'
            },
            'description': 'Subscription Manager'
        }
    ]
    
    print("🧪 Testing Containerized Lambda Functions")
    print("=" * 50)
    
    # First, list all functions to verify they exist
    try:
        response = lambda_client.list_functions()
        utility_functions = [
            f for f in response['Functions'] 
            if 'utility-customer-system-dev' in f['FunctionName']
        ]
        
        print(f"📋 Found {len(utility_functions)} utility functions:")
        for func in utility_functions:
            print(f"  • {func['FunctionName']} ({func['PackageType']}, {func.get('Runtime', 'Container')})")
        print()
        
    except Exception as e:
        print(f"❌ Error listing functions: {e}")
        return
    
    # Test each function
    results = []
    
    for test in tests:
        print(f"🧪 Testing: {test['description']}")
        print(f"   Function: {test['function_name']}")
        print(f"   Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            # Invoke the function
            start_time = time.time()
            
            response = lambda_client.invoke(
                FunctionName=test['function_name'],
                Payload=json.dumps(test['payload'])
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Parse response
            status_code = response['StatusCode']
            payload_response = json.loads(response['Payload'].read())
            
            # Check for errors
            if 'FunctionError' in response:
                print(f"   ❌ Function Error: {response['FunctionError']}")
                print(f"   📄 Error Response: {payload_response}")
                results.append({
                    'test': test['description'],
                    'status': 'FAILED',
                    'error': payload_response
                })
            else:
                print(f"   ✅ SUCCESS (Status: {status_code})")
                print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
                
                # Parse the response body if it's a string
                if isinstance(payload_response.get('body'), str):
                    try:
                        body = json.loads(payload_response['body'])
                        print(f"   📄 Response: {json.dumps(body, indent=6)}")
                    except:
                        print(f"   📄 Response: {payload_response}")
                else:
                    print(f"   📄 Response: {json.dumps(payload_response, indent=6)}")
                
                results.append({
                    'test': test['description'],
                    'status': 'SUCCESS',
                    'execution_time': execution_time,
                    'response': payload_response
                })
                
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            results.append({
                'test': test['description'],
                'status': 'ERROR',
                'error': str(e)
            })
        
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 30)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    total_count = len(results)
    
    for result in results:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        
        if result['status'] == 'SUCCESS' and 'execution_time' in result:
            print(f"   ⏱️  {result['execution_time']:.2f}s")
    
    print()
    print(f"🎯 Overall Result: {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        print("🎉 All containerized Lambda functions are working perfectly!")
    else:
        print("⚠️  Some functions need attention")
    
    return results

if __name__ == "__main__":
    test_containerized_lambdas()