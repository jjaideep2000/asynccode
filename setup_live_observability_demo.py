#!/usr/bin/env python3
"""
Live Observability Demo Setup
Creates real-time CloudWatch dashboard for customer demonstrations
"""

import boto3
import json
import time
from datetime import datetime

def create_live_demo_dashboard():
    """Create a real-time CloudWatch dashboard for live customer demo"""
    
    cloudwatch = boto3.client('cloudwatch')
    
    dashboard_body = {
        "widgets": [
            {
                "type": "log",
                "x": 0,
                "y": 0,
                "width": 24,
                "height": 8,
                "properties": {
                    "query": "SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'\n| fields @timestamp, @message\n| filter @message like /CUSTOMER_EVENT/\n| sort @timestamp desc\n| limit 50",
                    "region": "us-east-2",
                    "title": "🔴 LIVE: Customer Events (Real-Time)",
                    "view": "table"
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 8,
                "width": 12,
                "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'\n| filter @message like /CUSTOMER_EVENT/\n| parse @message /\"event_type\":\\s*\"(?<event_type>[^\"]*)\"/\n| parse @message /\"status\":\\s*\"(?<status>[^\"]*)\"/\n| stats count() by event_type, status\n| sort count desc",
                    "region": "us-east-2",
                    "title": "Event Types & Status (Last 15 min)",
                    "view": "table"
                }
            },
            {
                "type": "log",
                "x": 12,
                "y": 8,
                "width": 12,
                "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'\n| filter @message like /CUSTOMER_ERROR/\n| parse @message /\"customer_id\":\\s*\"(?<customer_id>[^\"]*)\"/\n| parse @message /\"error_type\":\\s*\"(?<error_type>[^\"]*)\"/\n| fields @timestamp, customer_id, error_type\n| sort @timestamp desc\n| limit 20",
                    "region": "us-east-2",
                    "title": "Recent Errors",
                    "view": "table"
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 14,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'\n| filter @message like /CUSTOMER_METRIC/\n| parse @message /\"duration_ms\":\\s*(?<duration_ms>[0-9.]+)/\n| parse @message /\"operation\":\\s*\"(?<operation>[^\"]*)\"/\n| stats avg(duration_ms), max(duration_ms), count() by bin(1m), operation\n| sort @timestamp desc",
                    "region": "us-east-2",
                    "title": "Performance Metrics (Real-Time)",
                    "view": "table"
                }
            }
        ]
    }
    
    try:
        response = cloudwatch.put_dashboard(
            DashboardName='LiveObservabilityDemo',
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print("Live Observability Dashboard Created!")
        print(f"Dashboard URL: https://us-east-2.console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=LiveObservabilityDemo")
        print("\nDemo Instructions:")
        print("1. Open the dashboard URL in a browser")
        print("2. Set auto-refresh to 10 seconds")
        print("3. Run customer transactions while showing the dashboard")
        print("4. Watch real-time events appear as customers use the system")
        
        return True
        
    except Exception as e:
        print(f"Failed to create dashboard: {e}")
        return False

def setup_live_demo_environment():
    """Ensure the system is ready for live demo"""
    
    print("SETTING UP LIVE OBSERVABILITY DEMO")
    print("=" * 50)
    
    # 1. Create dashboard
    dashboard_created = create_live_demo_dashboard()
    
    if not dashboard_created:
        return False
    
    # 2. Verify Lambda functions are ready
    lambda_client = boto3.client('lambda')
    
    functions_to_check = [
        'utility-customer-system-dev-bank-account-setup',
        'utility-customer-system-dev-payment-processing',
        'utility-customer-system-dev-bank-account-observability'
    ]
    
    print("\nVerifying Lambda Functions:")
    for function_name in functions_to_check:
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            print(f"   {function_name}: Ready")
        except Exception as e:
            print(f"   {function_name}: Not found - {e}")
    
    # 3. Check subscription status
    print("\nChecking Subscription Status:")
    for function_name in functions_to_check:
        try:
            response = lambda_client.list_event_source_mappings(FunctionName=function_name)
            for mapping in response['EventSourceMappings']:
                if 'sqs' in mapping['EventSourceArn'].lower():
                    state = mapping['State']
                    print(f"   {function_name}: {state}")
        except Exception as e:
            print(f"   {function_name}: Could not check subscriptions")
    
    print("\nLIVE DEMO READY!")
    print("=" * 30)
    print("Next Steps:")
    print("1. Open CloudWatch Dashboard (URL above)")
    print("2. Run: python3 live_customer_simulation.py")
    print("3. Watch real-time observability in action!")
    
    return True

if __name__ == "__main__":
    setup_live_demo_environment()