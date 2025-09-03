#!/usr/bin/env python3
"""
Test the subscription manager specifically
"""

import boto3
import json

def test_subscription_manager():
    """Test the subscription manager function"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    print("🧪 Testing Subscription Manager")
    print("=" * 40)
    
    try:
        response = lambda_client.invoke(
            FunctionName='utility-customer-system-dev-subscription-manager',
            Payload=json.dumps({'action': 'status'})
        )
        
        payload_response = json.loads(response['Payload'].read())
        
        if 'FunctionError' in response:
            print(f"❌ Function Error: {response['FunctionError']}")
            print(f"📄 Error Response: {payload_response}")
        else:
            print(f"✅ SUCCESS (Status: {response['StatusCode']})")
            
            # Parse the response body
            if isinstance(payload_response.get('body'), str):
                try:
                    body = json.loads(payload_response['body'])
                    print(f"📄 Response: {json.dumps(body, indent=2)}")
                except:
                    print(f"📄 Response: {payload_response}")
            else:
                print(f"📄 Response: {json.dumps(payload_response, indent=2)}")
                
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")

if __name__ == "__main__":
    test_subscription_manager()