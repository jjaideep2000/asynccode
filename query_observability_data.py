#!/usr/bin/env python3
"""
Query CloudWatch Logs for Observability Data
Shows complete customer journey tracking and 500 error handling
"""

import boto3
import json
import time
from datetime import datetime, timedelta

def query_customer_journey(customer_id: str):
    """Query CloudWatch logs for specific customer journey"""
    
    print(f"CLOUDWATCH OBSERVABILITY QUERY")
    print(f"Customer ID: {customer_id}")
    print("=" * 60)
    
    logs_client = boto3.client('logs')
    log_group = '/aws/lambda/utility-customer-system-dev-bank-account-observability'
    
    # Query for the last hour
    start_time = int((time.time() - 3600) * 1000)  # 1 hour ago
    end_time = int(time.time() * 1000)  # Now
    
    try:
        # Query 1: All customer events
        print(f"\n1. CUSTOMER EVENTS for {customer_id}")
        print("-" * 50)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            filterPattern=f'CUSTOMER_EVENT "{customer_id}"',
            startTime=start_time,
            endTime=end_time,
            limit=50
        )
        
        customer_events = []
        for event in response['events']:
            try:
                # Extract JSON from log message
                message = event['message']
                if 'CUSTOMER_EVENT:' in message:
                    json_part = message.split('CUSTOMER_EVENT: ')[1]
                    event_data = json.loads(json_part)
                    event_data['log_timestamp'] = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
                    customer_events.append(event_data)
            except:
                continue
        
        # Sort by timestamp
        customer_events.sort(key=lambda x: x['timestamp'])
        
        for i, event in enumerate(customer_events, 1):
            print(f"  {i}. [{event['log_timestamp']}] {event['event_type']}")
            print(f"     Status: {event['status']}")
            if 'trace_id' in event:
                print(f"     Trace ID: {event['trace_id']}")
            if 'details' in event and isinstance(event['details'], dict):
                for key, value in event['details'].items():
                    print(f"     {key}: {value}")
            print()
        
        # Query 2: Error events
        print(f"\n2. ERROR EVENTS for {customer_id}")
        print("-" * 50)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            filterPattern=f'CUSTOMER_ERROR "{customer_id}"',
            startTime=start_time,
            endTime=end_time,
            limit=20
        )
        
        error_events = []
        for event in response['events']:
            try:
                message = event['message']
                if 'CUSTOMER_ERROR:' in message:
                    json_part = message.split('CUSTOMER_ERROR: ')[1]
                    error_data = json.loads(json_part)
                    error_data['log_timestamp'] = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
                    error_events.append(error_data)
            except:
                continue
        
        for i, error in enumerate(error_events, 1):
            print(f"  {i}. [{error['log_timestamp']}] {error['error_type']}")
            print(f"     Message: {error['error_message']}")
            if 'trace_id' in error:
                print(f"     Trace ID: {error['trace_id']}")
            print()
        
        # Query 3: Performance metrics
        print(f"\n3. PERFORMANCE METRICS for {customer_id}")
        print("-" * 50)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            filterPattern=f'CUSTOMER_METRIC "{customer_id}"',
            startTime=start_time,
            endTime=end_time,
            limit=20
        )
        
        metrics = []
        for event in response['events']:
            try:
                message = event['message']
                if 'CUSTOMER_METRIC:' in message:
                    json_part = message.split('CUSTOMER_METRIC: ')[1]
                    metric_data = json.loads(json_part)
                    metric_data['log_timestamp'] = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
                    metrics.append(metric_data)
            except:
                continue
        
        for i, metric in enumerate(metrics, 1):
            print(f"  {i}. [{metric['log_timestamp']}] {metric['operation']}")
            print(f"     Duration: {metric['duration_ms']:.2f}ms")
            print(f"     Status: {metric['status']}")
            if 'trace_id' in metric:
                print(f"     Trace ID: {metric['trace_id']}")
            print()
        
        # Query 4: Subscription control events
        print(f"\n4. SUBSCRIPTION CONTROL EVENTS")
        print("-" * 50)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            filterPattern='SUBSCRIPTION_DISABLED',
            startTime=start_time,
            endTime=end_time,
            limit=10
        )
        
        for i, event in enumerate(response['events'], 1):
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S')
            print(f"  {i}. [{timestamp}] {event['message'].strip()}")
        
        return len(customer_events), len(error_events), len(metrics)
        
    except Exception as e:
        print(f"Error querying CloudWatch: {e}")
        return 0, 0, 0

def run_cloudwatch_insights_query(customer_id: str):
    """Run CloudWatch Insights query for advanced analytics"""
    
    print(f"\n5. CLOUDWATCH INSIGHTS ANALYTICS")
    print("-" * 50)
    
    logs_client = boto3.client('logs')
    log_group = '/aws/lambda/utility-customer-system-dev-bank-account-observability'
    
    # CloudWatch Insights query
    query = f"""
    fields @timestamp, @message
    | filter @message like /{customer_id}/
    | parse @message /CUSTOMER_EVENT: (?<event_json>.*)/
    | parse event_json /"event_type":\s*"(?<event_type>[^"]*)"/
    | parse event_json /"status":\s*"(?<status>[^"]*)"/
    | parse event_json /"trace_id":\s*"(?<trace_id>[^"]*)"/
    | filter ispresent(event_type)
    | sort @timestamp asc
    | limit 50
    """
    
    try:
        # Start query
        start_time = int((time.time() - 3600) * 1000)  # 1 hour ago
        end_time = int(time.time() * 1000)  # Now
        
        response = logs_client.start_query(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            queryString=query
        )
        
        query_id = response['queryId']
        print(f"Started CloudWatch Insights query: {query_id}")
        
        # Wait for query to complete
        for _ in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            result = logs_client.get_query_results(queryId=query_id)
            
            if result['status'] == 'Complete':
                print(f"Query completed with {len(result['results'])} results")
                
                for i, row in enumerate(result['results'][:10], 1):  # Show first 10 results
                    row_data = {field['field']: field['value'] for field in row}
                    timestamp = row_data.get('@timestamp', 'N/A')
                    event_type = row_data.get('event_type', 'N/A')
                    status = row_data.get('status', 'N/A')
                    trace_id = row_data.get('trace_id', 'N/A')[:20] + '...' if row_data.get('trace_id') else 'N/A'
                    
                    print(f"  {i}. {timestamp} | {event_type} | {status} | {trace_id}")
                
                break
            elif result['status'] == 'Failed':
                print(f"Query failed: {result.get('statistics', {}).get('recordsMatched', 'Unknown error')}")
                break
        else:
            print("Query timed out")
            
    except Exception as e:
        print(f"CloudWatch Insights query error: {e}")

def show_customer_journey_summary(customer_id: str, events_count: int, errors_count: int, metrics_count: int):
    """Show summary of customer journey observability"""
    
    print(f"\n6. OBSERVABILITY SUMMARY")
    print("=" * 50)
    print(f"Customer ID: {customer_id}")
    print(f"Total Events Logged: {events_count}")
    print(f"Error Events: {errors_count}")
    print(f"Performance Metrics: {metrics_count}")
    
    print(f"\nCustomer Support Capabilities:")
    print(f"  ✓ Complete customer journey tracking")
    print(f"  ✓ Real-time error detection and classification")
    print(f"  ✓ Performance monitoring and bottleneck identification")
    print(f"  ✓ Subscription control and recovery tracking")
    print(f"  ✓ Full audit trail with trace correlation")
    
    print(f"\nCloudWatch Log Group: {'/aws/lambda/utility-customer-system-dev-bank-account-observability'}")
    print(f"Search Pattern: CUSTOMER_EVENT \"{customer_id}\"")

def main():
    """Main function to demonstrate CloudWatch observability queries"""
    
    # Use the customer ID from our recent 500 error demo
    customer_id = "ERROR500-OTEL-1756837633"  # From the complete journey demo
    
    print("This will query CloudWatch logs for the customer transaction we just processed")
    print("showing complete observability data including 500 error handling")
    
    # Query customer journey
    events_count, errors_count, metrics_count = query_customer_journey(customer_id)
    
    # Run CloudWatch Insights query
    run_cloudwatch_insights_query(customer_id)
    
    # Show summary
    show_customer_journey_summary(customer_id, events_count, errors_count, metrics_count)
    
    print(f"\nTo run these queries manually in AWS Console:")
    print(f"1. Go to CloudWatch → Log groups")
    print(f"2. Select: /aws/lambda/utility-customer-system-dev-bank-account-observability")
    print(f"3. Use filter: CUSTOMER_EVENT \"{customer_id}\"")
    print(f"4. Or use CloudWatch Insights with the queries shown above")

if __name__ == "__main__":
    main()