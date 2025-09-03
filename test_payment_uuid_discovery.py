#!/usr/bin/env python3
"""
Test script to debug payment service UUID discovery
"""

import json
import boto3

def test_payment_uuid_discovery():
 """Test payment service UUID discovery"""
 
 lambda_client = boto3.client('lambda')
 
 print("Testing Payment Service UUID Discovery")
 print("=" * 50)
 
 # Check what event source mappings exist for the payment function
 try:
 response = lambda_client.list_event_source_mappings(
 FunctionName='utility-customer-system-dev-payment-processing'
 )
 
 print(f"Found {len(response['EventSourceMappings'])} event source mappings:")
 
 for mapping in response['EventSourceMappings']:
 print(f"\nMapping Details:")
 print(f" UUID: {mapping['UUID']}")
 print(f" Event Source: {mapping['EventSourceArn']}")
 print(f" Function: {mapping['FunctionArn']}")
 print(f" State: {mapping['State']}")
 print(f" Last Modified: {mapping['LastModified']}")
 
 # Check if this is the SQS mapping
 if 'sqs' in mapping['EventSourceArn'].lower():
 print(f" This is the SQS mapping we need!")
 
 # Try to update this mapping to enabled
 print(f"\nAttempting to enable this mapping...")
 try:
 update_response = lambda_client.update_event_source_mapping(
 UUID=mapping['UUID'],
 Enabled=True
 )
 print(f" Update successful!")
 print(f" New State: {update_response['State']}")
 print(f" Updated: {update_response['LastModified']}")
 
 except Exception as update_error:
 print(f" Update failed: {update_error}")
 
 return response['EventSourceMappings']
 
 except Exception as e:
 print(f"Failed to list event source mappings: {e}")
 return None

if __name__ == "__main__":
 test_payment_uuid_discovery()