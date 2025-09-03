#!/usr/bin/env python3
"""
DEMO: Enable subscriptions if they were disabled from previous tests
"""

import json
import boto3
import time

# Configuration
SUBSCRIPTION_CONTROL_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"

def enable_all_subscriptions():
    """Send SNS message to enable all subscriptions"""
    
    print("ENABLING ALL SUBSCRIPTIONS")
    print("=" * 35)
    
    sns = boto3.client('sns')
    
    # Send enable message
    control_message = {
        'action': 'enable',
        'timestamp': time.time(),
        'source': 'demo_script'
    }
    
    try:
        response = sns.publish(
            TopicArn=SUBSCRIPTION_CONTROL_TOPIC_ARN,
            Message=json.dumps(control_message),
            Subject='Demo: Enable All Subscriptions'
        )
        
        print(f"Enable message sent successfully!")
        print(f" Message ID: {response['MessageId']}")
        print(f" Topic: Subscription Control")
        
        print(f"\nWaiting for subscriptions to be enabled...")
        time.sleep(10)
        
        # Check status
        lambda_client = boto3.client('lambda')
        functions = [
            ('Bank Account', 'utility-customer-system-dev-bank-account-setup'),
            ('Payment', 'utility-customer-system-dev-payment-processing')
        ]
        
        print(f"\nSubscription Status After Enable:")
        
        for service_name, function_name in functions:
            try:
                response = lambda_client.list_event_source_mappings(FunctionName=function_name)
                
                for mapping in response['EventSourceMappings']:
                    if 'sqs' in mapping['EventSourceArn'].lower():
                        state = mapping['State']
                        enabled = state == 'Enabled'
                        print(f" {service_name}: {state} ({'' if enabled else ''})")
            
            except Exception as e:
                print(f" Error checking {service_name}: {e}")
        
        print(f"\nSubscription enable process complete!")
        
    except Exception as e:
        print(f"Failed to send enable message: {e}")

if __name__ == "__main__":
    enable_all_subscriptions()