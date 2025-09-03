#!/usr/bin/env python3
"""
Show Recent Observability Data
Display the actual observability data captured in recent executions
"""

import boto3
import json
from datetime import datetime, timedelta

def show_recent_observability_data():
    """Show recent observability data from CloudWatch logs"""
    
    print("RECENT OBSERVABILITY DATA")
    print("=" * 60)
    print("Here's the actual observability data captured from recent executions:")
    print()
    
    logs_client = boto3.client('logs')
    
    # Look at the last 2 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=2)
    
    log_group = '/aws/lambda/utility-customer-system-dev-bank-account-setup'
    
    try:
        # Get recent log streams
        streams_response = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=3
        )
        
        customer_events = []
        error_events = []
        metrics = []
        
        for stream in streams_response.get('logStreams', []):
            stream_name = stream['logStreamName']
            
            try:
                # Get events from this stream
                events_response = logs_client.get_log_events(
                    logGroupName=log_group,
                    logStreamName=stream_name,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000)
                )
                
                for event in events_response.get('events', []):
                    message = event['message'].strip()
                    
                    if 'CUSTOMER_EVENT:' in message:
                        try:
                            event_data = json.loads(message.split('CUSTOMER_EVENT: ')[1])
                            customer_events.append(event_data)
                        except:
                            pass
                    
                    elif 'CUSTOMER_ERROR:' in message:
                        try:
                            error_data = json.loads(message.split('CUSTOMER_ERROR: ')[1])
                            error_events.append(error_data)
                        except:
                            pass
                    
                    elif 'CUSTOMER_METRIC:' in message:
                        try:
                            metric_data = json.loads(message.split('CUSTOMER_METRIC: ')[1])
                            metrics.append(metric_data)
                        except:
                            pass
            
            except Exception as e:
                continue
        
        # Display the data
        print("CUSTOMER EVENTS CAPTURED:")
        print("-" * 40)
        
        if customer_events:
            # Group by customer and trace
            customers = {}
            for event in customer_events:
                customer_id = event.get('customer_id', 'unknown')
                if customer_id not in customers:
                    customers[customer_id] = []
                customers[customer_id].append(event)
            
            for customer_id, events in customers.items():
                print(f"\nCustomer: {customer_id}")
                print(f"   Events: {len(events)}")
                
                # Show the journey
                for event in sorted(events, key=lambda x: x.get('timestamp', '')):
                    event_type = event.get('event_type', 'unknown')
                    status = event.get('status', 'unknown')
                    timestamp = event.get('timestamp', '')[:19]
                    
                    if event_type == 'message_received':
                        print(f"   {timestamp}: Message received from {event.get('source', 'unknown')}")
                    elif event_type == 'validation_started':
                        print(f"   {timestamp}: Validation started")
                    elif event_type == 'validation_completed':
                        checks = event.get('validation_checks_passed', 0)
                        print(f"   {timestamp}: Validation completed ({checks} checks passed)")
                    elif event_type == 'bank_setup_started':
                        routing = event.get('routing_number', 'unknown')
                        print(f"   {timestamp}: Bank setup started (routing: {routing})")
                    elif event_type == 'external_validation_completed':
                        duration = event.get('duration_ms', 0)
                        score = event.get('validation_score', 0)
                        print(f"   {timestamp}: External validation completed ({duration:.1f}ms, score: {score})")
                    elif event_type == 'account_created':
                        account_id = event.get('account_id', 'unknown')
                        print(f"   {timestamp}: Account created ({account_id})")
                    elif event_type == 'bank_account_setup_completed':
                        duration = event.get('processing_duration_ms', 0)
                        print(f"   {timestamp}: Setup completed ({duration:.1f}ms total)")
                    else:
                        print(f"   {timestamp}: {event_type} - {status}")
        else:
            print("   No customer events found in recent logs")
        
        print(f"\nERROR EVENTS:")
        print("-" * 20)
        
        if error_events:
            for error in error_events:
                customer_id = error.get('customer_id', 'unknown')
                error_type = error.get('error_type', 'unknown')
                error_message = error.get('error_message', 'unknown')
                timestamp = error.get('timestamp', '')[:19]
                
                print(f"   {timestamp}: {customer_id}")
                print(f"      Type: {error_type}")
                print(f"      Message: {error_message[:100]}...")
        else:
            print("   No errors found in recent logs")
        
        print(f"\nPERFORMANCE METRICS:")
        print("-" * 25)
        
        if metrics:
            for metric in metrics:
                customer_id = metric.get('customer_id', 'unknown')
                operation = metric.get('operation', 'unknown')
                duration = metric.get('duration_ms', 0)
                status = metric.get('status', 'unknown')
                timestamp = metric.get('timestamp', '')[:19]
                
                print(f"   {timestamp}: {customer_id}")
                print(f"      Operation: {operation}")
                print(f"      Duration: {duration:.1f}ms")
                print(f"      Status: {status}")
        else:
            print("   No metrics found in recent logs")
        
        print(f"\nSUMMARY:")
        print("-" * 15)
        print(f"   Total Customer Events: {len(customer_events)}")
        print(f"   Total Errors: {len(error_events)}")
        print(f"   Total Metrics: {len(metrics)}")
        print(f"   Unique Customers: {len(set(e.get('customer_id') for e in customer_events))}")
        
    except Exception as e:
        print(f"Error retrieving observability data: {e}")

if __name__ == "__main__":
    show_recent_observability_data()
    print("\nObservability data display complete!")