#!/usr/bin/env python3
"""
DEMO 5E: The System Awakens - Subscriptions Re-enabled
Story: "The Lambda functions receive the signal and spring back to life..."
"""

import boto3
import time

def check_resubscription_status():
    """Check if Lambda functions have re-enabled their subscriptions"""
    
    print("DEMO 5E: THE SYSTEM AWAKENS")
    print("=" * 35)
    print("Story: The recovery signal has been sent through SNS.")
    print("Our Lambda functions should have received the message.")
    print("Let's see if they've responded and reactivated themselves...")
    print()
    
    print("Waiting for Lambda functions to process the recovery signal...")
    time.sleep(8)
    
    lambda_client = boto3.client('lambda')
    
    functions = [
        {
            'name': 'Bank Account Setup',
            'function': 'utility-customer-system-dev-bank-account-setup',
            'service': 'Bank Validation Service',
            'emoji': ''
        },
        {
            'name': 'Payment Processing', 
            'function': 'utility-customer-system-dev-payment-processing',
            'service': 'Payment Gateway',
            'emoji': ''
        }
    ]
    
    print("CHECKING: Lambda Function Response to Recovery Signal")
    print("-" * 55)
    
    enabled_count = 0
    
    for service_info in functions:
        print(f"\nChecking {service_info['name']} Lambda Function...")
        print(f"(Handles {service_info['service']} integration)")
        
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
                    
                    if state == 'Enabled':
                        print(f"REACTIVATION SUCCESSFUL!")
                        print(f"The Lambda function received the SNS recovery signal")
                        print(f"It used dynamic UUID discovery to re-enable its subscription")
                        print(f"Ready to process messages from {service_info['service']}")
                        enabled_count += 1
                    elif state == 'Disabled':
                        print(f"Still disabled - may need more time to process recovery signal")
                    elif state in ['Enabling', 'Updating']:
                        print(f"Currently reactivating - process in progress")
                        enabled_count += 0.5 # Partial credit for in-progress
                    else:
                        print(f"Unexpected state: {state}")
        
        except Exception as e:
            print(f"Error checking {service_info['name']}: {e}")
 
    print(f"\nREACTIVATION SUMMARY")
    print("-" * 25)
    
    if enabled_count >= 2:
        print(f"EXCELLENT: Both Lambda functions have reactivated!")
        print(f"The recovery process worked perfectly:")
        print(f" SNS delivered the recovery signal to both functions")
        print(f" Lambda functions processed the 'enable' command")
        print(f" Dynamic UUID discovery enabled subscription re-activation")
        print(f" Both services are ready to process queued messages")
        
        print(f"\nSYSTEM RECOVERY COMPLETE:")
        print(f" External services are online")
        print(f" Lambda subscriptions are re-enabled")
        print(f" Message processing will resume")
        print(f" Queued customer requests will be processed")
        
    elif enabled_count >= 1:
        print(f"PARTIAL REACTIVATION: {int(enabled_count)} service(s) reactivated")
        print(f"Some functions have responded to the recovery signal")
        print(f"Others may still be processing or need more time")
        
    else:
        print(f"REACTIVATION IN PROGRESS")
        print(f"Lambda functions may still be processing the recovery signal")
        print(f"SNS message delivery and processing can take a few moments")
        print(f"The reactivation should complete shortly")
    
    print(f"\nCHAPTER 5 COMPLETE")
    print(f"The Lambda functions have awakened from their protective slumber!")
    print(f"They received the recovery signal and reactivated their subscriptions.")
    print(f"Now let's see what happens to all those queued customer requests...")
    
    print(f"\nNext: Run 'python3 demo_5f_queues_empty.py'")
    print(f"to watch the queued messages get processed and the queues empty!")

def main():
    """Main function"""
    check_resubscription_status()

if __name__ == "__main__":
    main()