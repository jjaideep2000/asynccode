#!/usr/bin/env python3
"""
Setup SNS Subscription for Observability Lambda
Adds subscription control capability to the observability Lambda
"""

import boto3
import json

def setup_sns_subscription():
    """Add SNS subscription for subscription control to observability Lambda"""
    
    print("SETTING UP SNS SUBSCRIPTION FOR OBSERVABILITY LAMBDA")
    print("=" * 60)
    
    # Configuration
    function_name = "utility-customer-system-dev-bank-account-observability"
    topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
    
    try:
        # Initialize AWS clients
        sns_client = boto3.client('sns')
        lambda_client = boto3.client('lambda')
        
        # Get Lambda function ARN
        response = lambda_client.get_function(FunctionName=function_name)
        function_arn = response['Configuration']['FunctionArn']
        
        print(f"Lambda Function: {function_name}")
        print(f"Function ARN: {function_arn}")
        print(f"SNS Topic: {topic_arn}")
        
        # Check if subscription already exists
        print("\nChecking existing subscriptions...")
        subscriptions = sns_client.list_subscriptions_by_topic(TopicArn=topic_arn)
        
        existing_subscription = None
        for sub in subscriptions['Subscriptions']:
            if sub['Endpoint'] == function_arn and sub['Protocol'] == 'lambda':
                existing_subscription = sub
                break
        
        if existing_subscription:
            print(f"Subscription already exists: {existing_subscription['SubscriptionArn']}")
        else:
            # Create SNS subscription
            print("\nCreating SNS subscription...")
            subscription_response = sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol='lambda',
                Endpoint=function_arn
            )
            
            subscription_arn = subscription_response['SubscriptionArn']
            print(f"Created subscription: {subscription_arn}")
        
        # Add Lambda permission for SNS to invoke the function
        print("\nSetting up Lambda permissions...")
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='AllowExecutionFromSNSObservability',
                Action='lambda:InvokeFunction',
                Principal='sns.amazonaws.com',
                SourceArn=topic_arn
            )
            print("Added Lambda permission for SNS")
        except lambda_client.exceptions.ResourceConflictException:
            print("Lambda permission already exists")
        
        print("\nSNS SUBSCRIPTION SETUP COMPLETE!")
        print("\nThe observability Lambda can now receive:")
        print("  - SQS messages (bank account processing)")
        print("  - SNS messages (subscription control)")
        print("\nThis enables automatic subscription management!")
        
    except Exception as e:
        print(f"Error setting up SNS subscription: {e}")
        return False
    
    return True

def test_subscription():
    """Test the SNS subscription by sending a test control message"""
    
    print("\n" + "=" * 60)
    print("TESTING SNS SUBSCRIPTION")
    print("=" * 60)
    
    try:
        sns_client = boto3.client('sns')
        topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
        
        # Send test message
        test_message = {
            'action': 'test',
            'source': 'observability_setup_script',
            'timestamp': '2025-09-02T18:45:00Z',
            'customer_context': 'test-setup'
        }
        
        print("Sending test control message...")
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=json.dumps(test_message),
            Subject='Test: Observability Lambda SNS Subscription'
        )
        
        print(f"Test message sent: {response['MessageId']}")
        print("\nCheck CloudWatch logs for the observability Lambda to verify it received the message")
        
    except Exception as e:
        print(f"Error testing subscription: {e}")

if __name__ == "__main__":
    success = setup_sns_subscription()
    
    if success:
        test_subscription()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Deploy the updated Lambda code")
    print("2. Run the complete customer journey demo")
    print("3. Verify automatic subscription re-enablement works")