#!/usr/bin/env python3
"""
Check Lambda logs with extended time window
"""

import boto3
from datetime import datetime, timedelta

def check_extended_logs():
    """Check Lambda logs with a longer time window"""
    
    print("EXTENDED LAMBDA LOG CHECK")
    print("=" * 50)
    
    logs_client = boto3.client('logs')
    
    # Check logs from the last 30 minutes
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=30)
    
    log_groups = [
        '/aws/lambda/utility-customer-system-dev-bank-account-setup',
        '/aws/lambda/utility-customer-system-dev-payment-processing',
        '/aws/lambda/utility-customer-system-dev-bank-account-observability'
    ]
    
    for log_group in log_groups:
        print(f"\n{log_group.split('/')[-1]}:")
        print("-" * 40)
        
        try:
            # Get log streams
            streams_response = logs_client.describe_log_streams(
                logGroupName=log_group,
                orderBy='LastEventTime',
                descending=True,
                limit=5
            )
            
            found_events = False
            
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
                    
                    events = events_response.get('events', [])
                    
                    if events:
                        found_events = True
                        print(f"   Stream: {stream_name}")
                        
                        for event in events[-10:]:  # Show last 10 events
                            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                            message = event['message'].strip()
                            
                            # Highlight important messages
                            if 'CUSTOMER_EVENT' in message:
                                print(f"   EVENT {timestamp}: {message}")
                            elif 'ERROR' in message or 'Exception' in message:
                                print(f"   ERROR {timestamp}: {message}")
                            elif 'START' in message or 'END' in message:
                                print(f"   {timestamp}: {message}")
                            else:
                                print(f"   {timestamp}: {message}")
                
                except Exception as e:
                    print(f"   Error reading stream {stream_name}: {e}")
            
            if not found_events:
                print("   No log events found in any streams")
        
        except Exception as e:
            print(f"   Error accessing log group: {e}")

if __name__ == "__main__":
    check_extended_logs()
    print("\nExtended log check complete!")