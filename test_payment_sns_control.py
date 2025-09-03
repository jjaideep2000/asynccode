#!/usr/bin/env python3
"""
Test script to debug payment service SNS control message handling
"""

import json
import boto3

def test_payment_sns_control():
 """Test payment service with SNS control message"""
 
 lambda_client = boto3.client('lambda')
 
 # Create test SNS event
 test_event = {
 "Records": [
 {
 "EventSource": "aws:sns",
 "Sns": {
 "Message": json.dumps({
 "action": "enable",
 "timestamp": "2025-09-02T01:30:00.000000",
 "operator": "debug_test",
 "reason": "Testing payment service SNS control"
 }),
 "Subject": "Subscription Control",
 "TopicArn": "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
 }
 }
 ]
 }
 
 print("Testing Payment Service SNS Control Message")
 print("=" * 50)
 print(f"Test Event: {json.dumps(test_event, indent=2)}")
 
 try:
 # Invoke payment processing function
 response = lambda_client.invoke(
 FunctionName='utility-customer-system-dev-payment-processing',
 InvocationType='RequestResponse',
 Payload=json.dumps(test_event)
 )
 
 # Parse response
 payload = json.loads(response['Payload'].read())
 
 print(f"\nFunction Response:")
 print(f"Status Code: {response['StatusCode']}")
 print(f"Payload: {json.dumps(payload, indent=2)}")
 
 # Check if there were any errors
 if 'errorMessage' in payload:
 print(f"\nError Found: {payload['errorMessage']}")
 if 'errorType' in payload:
 print(f"Error Type: {payload['errorType']}")
 if 'stackTrace' in payload:
 print(f"📚 Stack Trace: {payload['stackTrace']}")
 
 return payload
 
 except Exception as e:
 print(f"Failed to invoke function: {e}")
 return None

if __name__ == "__main__":
 test_payment_sns_control()