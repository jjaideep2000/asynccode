#!/usr/bin/env python3
"""
DEMO 5B: The Intelligent Response - Subscriptions Auto-Disabled
Story: "The system detects the failures and intelligently protects itself..."
"""

import boto3
import time

def check_subscription_status():
    """Check if subscriptions were disabled by 500 errors"""
    
    print("DEMO 5B: THE INTELLIGENT RESPONSE")
    print("=" * 45)
    print("Story: Our Lambda functions have processed the failed requests.")
    print("They detected 500 errors from external services.")
    print("Now let's see how our intelligent system responded...")
    print()
    
    lambda_client = boto3.client('lambda')
    
    functions = [
        {
            'name': 'Bank Account Setup',
            'function': 'utility-customer-system-dev-bank-account-setup',
            'service': 'Bank Validation Service'
        },
        {
            'name': 'Payment Processing', 
            'function': 'utility-customer-system-dev-payment-processing',
            'service': 'Payment Gateway'
        }
    ]
    
    print("INVESTIGATING: System Response to 500 Errors")
    print("-" * 50)
    
    disabled_count = 0
    
    for service_info in functions:
        print(f"\nChecking {service_info['name']} Lambda Function...")
        print(f"(This handles {service_info['service']} integration)")
        
        try:
            response = lambda_client.list_event_source_mappings(
                FunctionName=service_info['function']
            )
            
            for mapping in response['EventSourceMappings']:
                if 'sqs' in mapping['EventSourceArn'].lower():
                    state = mapping['State']
                    uuid = mapping['UUID']
                    
                    print(f"Subscription Status: {state}")
                    print(f"Event Source Mapping UUID: {uuid}")
                    
                    if state == 'Disabled':
                        print(f"INTELLIGENT PROTECTION ACTIVATED!")
                        print(f"The Lambda function detected 500 errors from {service_info['service']}")
                        print(f"It automatically disabled its own subscription to prevent cascade failures!")
                        print(f"System is protecting itself - no more messages will be processed")
                        disabled_count += 1
                    elif state == 'Enabled':
                        print(f"Subscription still enabled - 500 error may not have been processed yet")
                    else:
                        print(f"Unexpected state: {state}")
        
        except Exception as e:
            print(f"Error checking {service_info['name']}: {e}")
 
    print(f"\nCRISIS RESPONSE SUMMARY")
    print("-" * 30)
    
    if disabled_count >= 2:
        print(f"EXCELLENT: Both services have intelligently disabled themselves!")
        print(f"The system detected external service failures (500 errors)")
        print(f"Lambda functions used dynamic UUID discovery to disable their subscriptions")
        print(f"This prevents cascade failures and protects system stability")
        
        print(f"\nPROTECTION MECHANISMS ACTIVATED:")
        print(f" No more messages will be processed until services recover")
        print(f" Existing messages are safely preserved in queues")
        print(f" System prevents resource exhaustion from failed retries")
        print(f" Cascade failures are prevented")
        
    elif disabled_count == 1:
        print(f"PARTIAL PROTECTION: {disabled_count} service disabled itself")
        print(f"One service detected the failure and protected itself")
        print(f"The other may still be processing or may not have encountered the error yet")
        
    else:
        print(f"WAITING: Services may still be processing the 500 errors")
        print(f"The intelligent protection may activate shortly")
        print(f"500 errors take a moment to be processed and trigger subscription disable")
    
    print(f"\nCHAPTER 2 COMPLETE")
    print(f"Our intelligent system has responded to the crisis!")
    print(f"The Lambda functions have protected themselves from cascade failures.")
    print(f"But what about new customer requests coming in?")
    
    print(f"\nNext: Run 'python3 demo_5c_messages_pile_up.py'")
    print(f"to see what happens when customers keep trying to use the system!")

def main():
    """Main function"""
    check_subscription_status()

if __name__ == "__main__":
    main()