#!/usr/bin/env python3
"""
Complete observability setup - SQS queue, SNS subscription, and Lambda trigger
"""

import boto3
import json

def main():
    print("Completing Observability Infrastructure Setup")
    print("=" * 50)
    
    # Step 1: Create SQS queue
    sqs = boto3.client('sqs')
    queue_name = "utility-customer-system-dev-bank-account-observability.fifo"
    
    try:
        response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = response['QueueUrl']
        print(f"Queue exists: {queue_url}")
    except sqs.exceptions.QueueDoesNotExist:
        print("Creating SQS queue...")
        response = sqs.create_queue(
            QueueName=queue_name,
            Attributes={
                'FifoQueue': 'true',
                'ContentBasedDeduplication': 'true',
                'VisibilityTimeout': '30',
                'MessageRetentionPeriod': '1209600'
            }
        )
        queue_url = response['QueueUrl']
        print(f"Created queue: {queue_url}")
    
    # Get queue ARN
    attrs = sqs.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['QueueArn']
    )
    queue_arn = attrs['Attributes']['QueueArn']
    print(f"Queue ARN: {queue_arn}")
    
    # Step 2: Set up Lambda trigger
    lambda_client = boto3.client('lambda')
    function_name = "utility-customer-system-dev-bank-account-observability"
    
    try:
        # Check if event source mapping exists
        mappings = lambda_client.list_event_source_mappings(FunctionName=function_name)
        
        existing_mapping = None
        for mapping in mappings['EventSourceMappings']:
            if queue_arn in mapping['EventSourceArn']:
                existing_mapping = mapping
                break
        
        if existing_mapping:
            print(f"Event source mapping exists: {existing_mapping['UUID']}")
        else:
            print("Creating event source mapping...")
            response = lambda_client.create_event_source_mapping(
                EventSourceArn=queue_arn,
                FunctionName=function_name,
                BatchSize=1,
                Enabled=True
            )
            print(f"Created mapping: {response['UUID']}")
            
    except Exception as e:
        print(f"Lambda trigger setup: {e}")
    
    # Step 3: Set up SNS subscription
    sns = boto3.client('sns')
    topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"
    
    try:
        # Set queue policy
        policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "sns.amazonaws.com"},
                "Action": "sqs:SendMessage",
                "Resource": queue_arn,
                "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}}
            }]
        }
        
        sqs.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={'Policy': json.dumps(policy)}
        )
        print("Set queue policy")
        
        # Create subscription
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='sqs',
            Endpoint=queue_arn,
            Attributes={
                'FilterPolicy': json.dumps({'observability_demo': ['true']}),
                'RawMessageDelivery': 'true'
            }
        )
        print(f"SNS subscription: {response['SubscriptionArn']}")
        
    except Exception as e:
        print(f"SNS setup: {e}")
    
    print("\nSetup complete! Ready to test observability.")

if __name__ == "__main__":
    main()