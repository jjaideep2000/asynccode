#!/usr/bin/env python3
"""
Live Log Stream Demo
Shows real-time customer events streaming as they happen
Perfect for customer demonstrations
"""

import boto3
import json
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict

class LiveLogStreamer:
    def __init__(self):
        self.logs_client = boto3.client('logs')
        self.running = False
        self.last_check_time = int((datetime.utcnow() - timedelta(minutes=1)).timestamp() * 1000)
        self.event_counts = defaultdict(int)
        
        self.log_groups = [
            '/aws/lambda/utility-customer-system-dev-bank-account-setup',
            '/aws/lambda/utility-customer-system-dev-payment-processing',
            '/aws/lambda/utility-customer-system-dev-bank-account-observability'
        ]
    
    def format_customer_event(self, event_data):
        """Format customer event for display"""
        try:
            # Parse the CUSTOMER_EVENT JSON
            if 'CUSTOMER_EVENT:' in event_data['message']:
                json_part = event_data['message'].split('CUSTOMER_EVENT: ')[1]
                event_json = json.loads(json_part)
                
                timestamp = datetime.fromtimestamp(event_data['timestamp'] / 1000).strftime('%H:%M:%S.%f')[:-3]
                customer_id = event_json.get('customer_id', 'unknown')[:20]
                event_type = event_json.get('event_type', 'unknown')
                status = event_json.get('status', 'unknown')
                service = event_json.get('service', 'unknown')
                
                # Status indicators
                if status == 'success':
                    status_icon = 'OK'
                elif status == 'error':
                    status_icon = 'ERR'
                elif status == 'processing':
                    status_icon = 'PROC'
                else:
                    status_icon = 'INFO'
                
                # Event type indicators
                event_icons = {
                    'message_received': 'MSG',
                    'validation_started': 'VAL',
                    'validation_completed': 'OK',
                    'validation_failed': 'FAIL',
                    'bank_setup_started': 'BANK',
                    'external_validation_completed': 'EXT',
                    'account_created': 'NEW',
                    'bank_account_setup_completed': 'DONE',
                    'demo_500_error_triggered': 'ERR',
                    'subscription_disabled': 'STOP',
                    'subscription_enabled': 'START',
                    'trace_started': 'BEGIN',
                    'trace_completed': 'END'
                }
                
                event_icon = event_icons.get(event_type, 'INFO')
                
                return f"{timestamp} {status_icon:<4} {event_icon:<5} {customer_id:<20} {event_type:<25} [{service}]"
                
        except Exception as e:
            # Fallback for non-JSON events
            timestamp = datetime.fromtimestamp(event_data['timestamp'] / 1000).strftime('%H:%M:%S.%f')[:-3]
            message = event_data['message'][:80] + "..." if len(event_data['message']) > 80 else event_data['message']
            return f"{timestamp} INFO {message}"
        
        return None
    
    def stream_logs_from_group(self, log_group):
        """Stream logs from a specific log group"""
        
        while self.running:
            try:
                current_time = int(datetime.utcnow().timestamp() * 1000)
                
                # Get recent events
                response = self.logs_client.filter_log_events(
                    logGroupName=log_group,
                    startTime=self.last_check_time,
                    endTime=current_time,
                    filterPattern='CUSTOMER_EVENT'
                )
                
                # Process and display events
                for event in response['events']:
                    formatted_event = self.format_customer_event(event)
                    if formatted_event:
                        print(formatted_event)
                        
                        # Count event types
                        if 'CUSTOMER_EVENT:' in event['message']:
                            try:
                                json_part = event['message'].split('CUSTOMER_EVENT: ')[1]
                                event_json = json.loads(json_part)
                                event_type = event_json.get('event_type', 'unknown')
                                self.event_counts[event_type] += 1
                            except:
                                pass
                
                self.last_check_time = current_time
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Error streaming from {log_group}: {e}")
                time.sleep(5)
    
    def display_statistics(self):
        """Display running statistics"""
        
        while self.running:
            time.sleep(30)  # Update stats every 30 seconds
            
            if self.event_counts:
                print(f"\nLIVE STATISTICS (Last 30 seconds)")
                print("-" * 50)
                
                total_events = sum(self.event_counts.values())
                print(f"Total Events: {total_events}")
                
                # Top event types
                sorted_events = sorted(self.event_counts.items(), key=lambda x: x[1], reverse=True)
                for event_type, count in sorted_events[:5]:
                    print(f"  {event_type}: {count}")
                
                print("-" * 50)
                
                # Reset counts
                self.event_counts.clear()
    
    def start_live_stream(self):
        """Start live log streaming"""
        
        self.running = True
        
        print(f"LIVE CUSTOMER EVENT STREAM")
        print("=" * 80)
        print(f"Monitoring: {len(self.log_groups)} Lambda functions")
        print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Tip: Run live_customer_simulation.py in another terminal")
        print("=" * 80)
        print(f"{'Time':<12} {'Status':<4} {'Type':<5} {'Customer ID':<20} {'Event Type':<25} {'Service'}")
        print("-" * 80)
        
        # Start streaming threads for each log group
        threads = []
        for log_group in self.log_groups:
            thread = threading.Thread(target=self.stream_logs_from_group, args=(log_group,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Start statistics thread
        stats_thread = threading.Thread(target=self.display_statistics)
        stats_thread.daemon = True
        stats_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\nStopping live stream...")
            self.running = False
            
            # Wait for threads to finish
            for thread in threads:
                thread.join(timeout=2)
            
            print(f"Live stream stopped")

def main():
    """Main function"""
    
    print(f"REAL-TIME OBSERVABILITY DEMO")
    print("=" * 50)
    print("This will show live customer events as they happen")
    print("Perfect for demonstrating observability to customers")
    print()
    print("Instructions:")
    print("1. Start this script")
    print("2. In another terminal, run: python3 live_customer_simulation.py")
    print("3. Watch real-time events stream in this window")
    print()
    
    input("Press Enter to start live streaming...")
    
    streamer = LiveLogStreamer()
    streamer.start_live_stream()

if __name__ == "__main__":
    main()