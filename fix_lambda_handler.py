#!/usr/bin/env python3
"""
Fix Lambda handler configuration
"""

import boto3

def fix_lambda_handler():
    """Fix the Lambda handler configuration"""
    
    print("FIXING LAMBDA HANDLER CONFIGURATION")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda')
    
    functions_to_fix = [
        'utility-customer-system-dev-bank-account-setup',
        'utility-customer-system-dev-payment-processing'
    ]
    
    for function_name in functions_to_fix:
        try:
            print(f"\nUpdating {function_name}")
            
            # Update the handler configuration
            response = lambda_client.update_function_configuration(
                FunctionName=function_name,
                Handler='lambda_function.lambda_handler'
            )
            
            print(f"Handler updated to: {response['Handler']}")
            print(f"   Last Modified: {response['LastModified']}")
            
        except Exception as e:
            print(f"Error updating {function_name}: {e}")

if __name__ == "__main__":
    fix_lambda_handler()
    print("\nHandler configuration fixed!")