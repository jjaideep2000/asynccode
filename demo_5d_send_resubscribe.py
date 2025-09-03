#!/usr/bin/env python3
"""
DEMO 5D: The Recovery Signal - Send Resubscribe Message
Story: "The external services are back online - time to signal recovery..."
"""

import json
import boto3
import time
from datetime import datetime

# Configuration
SUBSCRIPTION_CONTROL_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"

def main():
    """The Recovery Signal - External Services Are Back"""
    
    print("DEMO 5D: THE RECOVERY SIGNAL")
    print("=" * 35)
    print("Story: Good news! The external services have been restored.")
    print("The bank validation service and payment gateway are back online.")
    print("Now we need to tell our Lambda functions it's safe to resume processing...")
    print()
    
    print("OPERATIONS TEAM: Monitoring Dashboard Alert")
    print("-" * 50)
    print("Dashboard shows:")
    print(" Bank Validation Service: ONLINE")
    print(" Payment Gateway: ONLINE") 
    print(" All external dependencies restored")
    print(" Queue depth: Messages waiting for processing")
    print()
    
    print("The operations team decides it's time to resume processing.")
    print("They will send a resubscribe signal through the SNS control topic.")
    print()
    
    sns = boto3.client('sns')
    
    print("SENDING RECOVERY SIGNAL")
    print("-" * 30)
    
    # Create the recovery message
    recovery_message = {
        'action': 'enable',
        'timestamp': datetime.utcnow().isoformat(),
        'source': 'operations_team',
        'reason': 'external_services_restored',
        'operator': 'demo_user',
        'services_restored': [
            'bank_validation_service',
            'payment_gateway'
        ]
    }
    
    print(f"Recovery Message Details:")
    print(f" Action: {recovery_message['action']}")
    print(f" Timestamp: {recovery_message['timestamp']}")
    print(f" Operator: {recovery_message['operator']}")
    print(f" Reason: External services have been restored")
    
    print(f"\nPublishing to SNS Control Topic...")
    print(f"Topic: Subscription Control")
    print(f"ARN: {SUBSCRIPTION_CONTROL_TOPIC_ARN}")
    
    try:
        response = sns.publish(
            TopicArn=SUBSCRIPTION_CONTROL_TOPIC_ARN,
            Message=json.dumps(recovery_message, indent=2),
            Subject='System Recovery: Re-enable All Subscriptions',
            MessageAttributes={
                'action': {
                    'DataType': 'String',
                    'StringValue': 'enable'
                },
                'source': {
                    'DataType': 'String', 
                    'StringValue': 'operations_team'
                }
            }
        )
        
        print(f"\nRECOVERY SIGNAL SENT SUCCESSFULLY!")
        print(f"SNS Message ID: {response['MessageId']}")
        print(f"Message published to subscription control topic")
        
        print(f"\nWhat happens next:")
        print(f" SNS delivers the message to all subscribed Lambda functions")
        print(f" Each Lambda function receives the 'enable' command")
        print(f" Lambda functions will re-enable their SQS subscriptions")
        print(f" Message processing will resume automatically")
        
        print(f"\nThe recovery signal is now propagating through the system...")
        print(f"Lambda functions should receive and process this message shortly.")
        
    except Exception as e:
        print(f"FAILED TO SEND RECOVERY SIGNAL: {e}")
        return
    
    print(f"\nRECOVERY PROCESS INITIATED")
    print("-" * 35)
    print(f"External services confirmed online")
    print(f"Recovery signal sent via SNS")
    print(f"Lambda functions will be notified")
    print(f"Waiting for automatic resubscription...")
    
    print(f"\nCHAPTER 4 COMPLETE")
    print(f"The recovery signal has been sent!")
    print(f"Our Lambda functions should receive this message and reactivate.")
    print(f"Let's see if they respond to the recovery signal...")
    
    print(f"\nNext: Run 'python3 demo_5e_subscriptions_enabled.py'")
    print(f"to verify that the Lambda functions have resubscribed!")

if __name__ == "__main__":
    main()