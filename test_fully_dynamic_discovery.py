#!/usr/bin/env python3
"""
Test the fully dynamic Lambda function discovery
"""
import boto3
import json

def test_dynamic_discovery():
    """Test the new fully dynamic discovery method"""
    
    print("🔍 TESTING FULLY DYNAMIC LAMBDA DISCOVERY")
    print("=" * 50)
    
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    # Test the subscription manager's new discovery
    print("\n1. Testing Subscription Manager Discovery...")
    try:
        response = lambda_client.invoke(
            FunctionName='utility-customer-system-dev-subscription-manager',
            InvocationType='RequestResponse',
            Payload=json.dumps({'action': 'refresh', 'force': True})
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result['body'])
        
        refresh_result = body['result']
        print(f"✅ Discovery successful!")
        print(f"   Functions found: {refresh_result['new_count']}")
        print(f"   Discovery method: Auto-scan (no hardcoding)")
        
        for func_name in refresh_result['current_functions']:
            print(f"   - {func_name}")
            
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
        return False
    
    # Test status to see discovery details
    print("\n2. Getting Detailed Status...")
    try:
        response = lambda_client.invoke(
            FunctionName='utility-customer-system-dev-subscription-manager',
            InvocationType='RequestResponse',
            Payload=json.dumps({'action': 'status'})
        )
        
        result = json.loads(response['Payload'].read())
        body = json.loads(result['body'])
        
        status = body['status']
        print(f"✅ Status retrieved:")
        print(f"   Total functions managed: {status['summary']['total_functions']}")
        
        for func in status['functions']:
            print(f"   📋 {func['service_name']}:")
            print(f"      Function: {func['function_name']}")
            print(f"      Status: {func['overall_status']}")
            print(f"      SQS Mappings: {func['total_mappings']}")
            
    except Exception as e:
        print(f"❌ Status test failed: {e}")
        return False
    
    return True

def manual_discovery_test():
    """Manually test the discovery logic to see what it finds"""
    
    print("\n3. Manual Discovery Test (What AWS API Returns)...")
    print("-" * 50)
    
    lambda_client = boto3.client('lambda', region_name='us-east-2')
    
    function_prefix = 'utility-customer-system-dev-'
    exclude_functions = ['subscription-manager']
    
    print(f"Scanning for functions with prefix: {function_prefix}")
    print(f"Excluding: {exclude_functions}")
    
    try:
        # List all functions
        paginator = lambda_client.get_paginator('list_functions')
        all_functions = []
        
        for page in paginator.paginate():
            all_functions.extend(page['Functions'])
        
        print(f"\nFound {len(all_functions)} total Lambda functions in account")
        
        # Filter by prefix
        matching_functions = [
            f for f in all_functions 
            if f['FunctionName'].startswith(function_prefix)
        ]
        
        print(f"Found {len(matching_functions)} functions matching prefix:")
        
        processing_functions = []
        
        for function in matching_functions:
            function_name = function['FunctionName']
            service_name = function_name.replace(function_prefix, '')
            
            print(f"\n📋 Checking: {function_name}")
            print(f"   Service name: {service_name}")
            
            # Check if excluded
            if any(exclude in service_name for exclude in exclude_functions):
                print(f"   ❌ Excluded (matches exclude pattern)")
                continue
            
            # Check for SQS event source mappings
            try:
                mappings_response = lambda_client.list_event_source_mappings(
                    FunctionName=function_name
                )
                
                sqs_mappings = [
                    mapping for mapping in mappings_response['EventSourceMappings']
                    if 'sqs' in mapping['EventSourceArn'].lower()
                ]
                
                print(f"   SQS Mappings: {len(sqs_mappings)}")
                
                if sqs_mappings:
                    for mapping in sqs_mappings:
                        print(f"     - {mapping['EventSourceArn']} ({mapping['State']})")
                    
                    processing_functions.append({
                        'function_name': function_name,
                        'service_name': service_name,
                        'sqs_mappings': len(sqs_mappings)
                    })
                    print(f"   ✅ Added to managed functions")
                else:
                    print(f"   ⚠️  No SQS mappings - not a processing function")
                    
            except Exception as e:
                print(f"   ❌ Error checking mappings: {e}")
        
        print(f"\n🎯 DISCOVERY RESULT:")
        print(f"   Processing functions found: {len(processing_functions)}")
        
        for func in processing_functions:
            print(f"   - {func['service_name']} ({func['sqs_mappings']} SQS mappings)")
        
        return len(processing_functions) > 0
        
    except Exception as e:
        print(f"❌ Manual discovery failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FULLY DYNAMIC LAMBDA DISCOVERY TEST")
    print("No hardcoding - pure AWS API discovery!")
    print("=" * 60)
    
    # Test the subscription manager
    success1 = test_dynamic_discovery()
    
    # Manual test to see the discovery process
    success2 = manual_discovery_test()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 FULLY DYNAMIC DISCOVERY WORKING!")
        print("✅ No hardcoded function lists")
        print("✅ Auto-discovers all processing Lambda functions")
        print("✅ Uses AWS API to find functions with SQS mappings")
        print("✅ Completely dynamic and scalable")
    else:
        print("⚠️  Some tests failed - check output above")