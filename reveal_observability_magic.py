#!/usr/bin/env python3
"""
Reveal Observability Magic
Perfect script to run at the end of demo_5 sequence to show all the observability data
"""

import boto3
import json
import time
from datetime import datetime, timedelta

def reveal_observability_magic():
    """Reveal all the observability data captured during the demo"""
    
    print("REVEALING THE OBSERVABILITY MAGIC")
    print("=" * 60)
    print("You just watched our system handle a complete crisis and recovery.")
    print("But here's what you DIDN'T see...")
    print()
    print("Every single event was captured and tracked in real-time!")
    print("Let me show you the observability data from your demo...")
    print()
    
    input("Press Enter to reveal the magic...")
    
    logs_client = boto3.client('logs')
    
    # Look at last 10 minutes (should cover the demo_5 sequence)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=10)
    
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)
    
    print(f"\nSCANNING OBSERVABILITY DATA")
    print(f"Time Range: {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
    print("=" * 50)
    
    # Get all customer events from the demo
    log_group = '/aws/lambda/utility-customer-system-dev-bank-account-setup'
    
    try:
        print("Customer Events Captured During Demo:")
        print("-" * 40)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time_ms,
            endTime=end_time_ms,
            filterPattern='CUSTOMER_EVENT'
        )
        
        events_by_customer = {}
        
        for event in response['events']:
            if 'CUSTOMER_EVENT:' in event['message']:
                try:
                    json_part = event['message'].split('CUSTOMER_EVENT: ')[1]
                    event_data = json.loads(json_part)
                    
                    customer_id = event_data.get('customer_id', 'unknown')
                    event_type = event_data.get('event_type', 'unknown')
                    status = event_data.get('status', 'unknown')
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
                    
                    if customer_id not in events_by_customer:
                        events_by_customer[customer_id] = []
                    
                    events_by_customer[customer_id].append({
                        'timestamp': timestamp,
                        'event_type': event_type,
                        'status': status
                    })
                    
                except:
                    continue
        
        # Show customer journeys
        demo_customers = [k for k in events_by_customer.keys() if 'ERROR500' in k or 'normal-' in k]
        
        if demo_customers:
            print(f"Found {len(demo_customers)} customers from your demo!")
            print()
            
            for customer_id in demo_customers[:3]:  # Show first 3 customers
                events = events_by_customer[customer_id]
                events.sort(key=lambda x: x['timestamp'])
                
                print(f"Customer: {customer_id[:30]}...")
                for event in events:
                    status_icon = 'OK' if event['status'] == 'success' else 'ERR' if event['status'] == 'error' else 'PROC'
                    print(f"   {event['timestamp']} {status_icon} {event['event_type']}")
                print()
        
        print(f"TOTAL EVENTS CAPTURED: {len(response['events'])}")
        
    except Exception as e:
        print(f"Error retrieving customer events: {e}")
    
    # Show error events
    try:
        print(f"\nERROR EVENTS CAPTURED:")
        print("-" * 30)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time_ms,
            endTime=end_time_ms,
            filterPattern='CUSTOMER_ERROR'
        )
        
        error_count = 0
        for event in response['events']:
            if 'CUSTOMER_ERROR:' in event['message']:
                try:
                    json_part = event['message'].split('CUSTOMER_ERROR: ')[1]
                    error_data = json.loads(json_part)
                    
                    timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
                    customer_id = error_data.get('customer_id', 'unknown')[:25]
                    error_type = error_data.get('error_type', 'unknown')
                    
                    print(f"   {timestamp} ERR {customer_id} - {error_type}")
                    error_count += 1
                    
                except:
                    continue
        
        print(f"\nTOTAL ERRORS CAPTURED: {error_count}")
        
    except Exception as e:
        print(f"Error retrieving error events: {e}")
    
    # Show system protection events
    try:
        print(f"\nSYSTEM PROTECTION EVENTS:")
        print("-" * 35)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time_ms,
            endTime=end_time_ms,
            filterPattern='SUBSCRIPTION_DISABLED OR SUBSCRIPTION_ENABLED'
        )
        
        protection_events = 0
        for event in response['events']:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
            message = event['message']
            
            if 'SUBSCRIPTION_DISABLED' in message:
                print(f"   {timestamp} STOP System Protection Activated")
                protection_events += 1
            elif 'SUBSCRIPTION_ENABLED' in message:
                print(f"   {timestamp} START System Recovery Completed")
                protection_events += 1
        
        print(f"\nTOTAL PROTECTION EVENTS: {protection_events}")
        
    except Exception as e:
        print(f"Error retrieving system events: {e}")
    
    # Show the magic reveal
    print(f"\nTHE OBSERVABILITY MAGIC REVEALED!")
    print("=" * 50)
    print("While you were watching the demo, our system was:")
    print()
    print("- Tracking every customer interaction")
    print("- Monitoring all system components")
    print("- Measuring performance in real-time")
    print("- Detecting and classifying errors")
    print("- Logging system protection actions")
    print("- Recording recovery events")
    print("- Building complete audit trails")
    print()
    print("CUSTOMER SUPPORT BENEFITS:")
    print("   • 'What happened to customer XYZ?' - Instant answer")
    print("   • 'Why was processing slow at 2pm?' - Complete timeline")
    print("   • 'Were any customers affected by the outage?' - Full list")
    print("   • 'Is the system healthy now?' - Real-time status")
    print()
    print("BUSINESS VALUE:")
    print("   - Zero revenue loss during outages")
    print("   - Zero customer impact from system issues")
    print("   - Faster issue resolution (minutes vs hours)")
    print("   - Data-driven operational decisions")
    print("   - Complete compliance audit trail")
    print()
    print("This is the power of comprehensive observability!")
    print("Every event you just saw was captured, tracked, and made searchable.")

def show_cloudwatch_dashboard():
    """Show how to access the CloudWatch dashboard"""
    
    print(f"\nWANT TO SEE MORE?")
    print("=" * 30)
    print("All this data is available in real-time through:")
    print()
    print("CloudWatch Dashboard:")
    print("   https://us-east-2.console.aws.amazon.com/cloudwatch/home?region=us-east-2")
    print()
    print("Sample CloudWatch Queries:")
    print()
    print("   Find all events for a customer:")
    print('   SOURCE \'/aws/lambda/utility-customer-system-dev-bank-account-setup\'')
    print('   | filter @message like /CUSTOMER_EVENT/ and @message like /CUSTOMER_ID/')
    print()
    print("   Show error summary:")
    print('   SOURCE \'/aws/lambda/utility-customer-system-dev-bank-account-setup\'')
    print('   | filter @message like /CUSTOMER_ERROR/')
    print('   | stats count() by error_type')
    print()
    print("   Performance analysis:")
    print('   SOURCE \'/aws/lambda/utility-customer-system-dev-bank-account-setup\'')
    print('   | filter @message like /CUSTOMER_METRIC/')
    print('   | stats avg(duration_ms) by operation')

def main():
    """Main function"""
    
    print("DEMO OBSERVABILITY REVEAL")
    print("=" * 40)
    print("Perfect script to run after your demo_5 sequence!")
    print("This will show all the observability data that was")
    print("captured during your demonstration.")
    print()
    
    reveal_observability_magic()
    
    print(f"\n" + "="*60)
    show_cloudwatch_dashboard()
    
    print(f"\nOBSERVABILITY DEMONSTRATION COMPLETE!")
    print("Thank you for experiencing the power of comprehensive observability!")

if __name__ == "__main__":
    main()