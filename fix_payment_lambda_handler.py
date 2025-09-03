#!/usr/bin/env python3
"""
Fix Payment Lambda Handler Configuration
The Lambda function is looking for 'lambda_function' but the handler is in 'handler.py'
"""

import boto3
import json

def fix_lambda_handler():
    """Fix the Lambda function handler configuration"""
    
    lambda_client = boto3.client('lambda')
    
    function_name = "utility-customer-system-dev-payment-processing"
    
    print("=== FIXING PAYMENT LAMBDA HANDLER ===")
    
    try:
        # Get current configuration
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        
        current_handler = config.get('Handler', 'N/A')
        print(f"Current Handler: {current_handler}")
        
        # The correct handler should be 'handler.lambda_handler' based on our file structure
        correct_handler = "handler.lambda_handler"
        
        if current_handler != correct_handler:
            print(f"Updating handler from '{current_handler}' to '{correct_handler}'")
            
            response = lambda_client.update_function_configuration(
                FunctionName=function_name,
                Handler=correct_handler
            )
            
            print("✅ Handler updated successfully!")
            print(f"New Handler: {response['Handler']}")
            
        else:
            print("✅ Handler is already correct")
            
    except Exception as e:
        print(f"❌ Error fixing handler: {e}")

def check_event_source_mapping():
    """Check and potentially re-enable the SQS event source mapping"""
    
    lambda_client = boto3.client('lambda')
    
    function_name = "utility-customer-system-dev-payment-processing"
    
    print("\n=== CHECKING EVENT SOURCE MAPPING ===")
    
    try:
        mappings = lambda_client.list_event_source_mappings(FunctionName=function_name)
        
        for mapping in mappings['EventSourceMappings']:
            uuid = mapping['UUID']
            state = mapping['State']
            source_arn = mapping.get('EventSourceArn', 'N/A')
            
            print(f"Mapping UUID: {uuid}")
            print(f"State: {state}")
            print(f"Source: {source_arn}")
            
            if state == 'Disabled':
                print("⚠️  Event source mapping is disabled")
                
                # Ask if we should re-enable it
                print("The mapping was likely disabled due to 500 errors.")
                print("After fixing the handler, we should re-enable it.")
                
                try:
                    response = lambda_client.update_event_source_mapping(
                        UUID=uuid,
                        Enabled=True
                    )
                    
                    print("✅ Event source mapping re-enabled!")
                    print(f"New State: {response['State']}")
                    
                except Exception as e:
                    print(f"❌ Error re-enabling mapping: {e}")
                    
            else:
                print("✅ Event source mapping is enabled")
                
    except Exception as e:
        print(f"❌ Error checking event source mappings: {e}")

def test_fixed_lambda():
    """Test the Lambda function after fixing"""
    
    lambda_client = boto3.client('lambda')
    
    function_name = "utility-customer-system-dev-payment-processing"
    
    print("\n=== TESTING FIXED LAMBDA ===")
    
    test_payload = {
        "customer_id": "test-customer-fix-123",
        "amount": 50.00,
        "payment_method": "bank_account",
        "message_id": "test-fix-message-123"
    }
    
    try:
        print("Testing Lambda function with sample payload...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        status_code = response['StatusCode']
        payload = json.loads(response['Payload'].read())
        
        print(f"Status Code: {status_code}")
        print(f"Response: {json.dumps(payload, indent=2)}")
        
        if status_code == 200 and 'errorMessage' not in payload:
            print("✅ Lambda function is now working correctly!")
        else:
            print("❌ Lambda function still has issues")
            
    except Exception as e:
        print(f"❌ Error testing Lambda function: {e}")

if __name__ == "__main__":
    print("Fixing Payment Lambda Handler Configuration")
    print("=" * 60)
    
    fix_lambda_handler()
    check_event_source_mapping()
    test_fixed_lambda()
    
    print("\n" + "=" * 60)
    print("Fix complete! The stuck messages should now be processed.")