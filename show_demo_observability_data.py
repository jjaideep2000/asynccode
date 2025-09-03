#!/usr/bin/env python3
"""
Show Demo Observability Data
Displays all observability data captured during the demo_5 sequence
Perfect for revealing the "behind the scenes" observability after the demo
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter

class DemoObservabilityAnalyzer:
    def __init__(self, demo_start_time=None):
        self.logs_client = boto3.client('logs')
        self.cloudwatch = boto3.client('cloudwatch')
        
        # If no start time provided, look at last 30 minutes
        if demo_start_time:
            self.demo_start_time = demo_start_time
        else:
            self.demo_start_time = datetime.utcnow() - timedelta(minutes=30)
        
        self.demo_end_time = datetime.utcnow()
        
        self.log_groups = [
            '/aws/lambda/utility-customer-system-dev-bank-account-setup',
            '/aws/lambda/utility-customer-system-dev-payment-processing',
            '/aws/lambda/utility-customer-system-dev-bank-account-observability'
        ]
        
        # Store all events for analysis
        self.all_events = []
        self.customer_journeys = defaultdict(list)
        self.error_events = []
        self.performance_metrics = []
        self.system_events = []
    
    def collect_demo_data(self):
        """Collect all observability data from the demo period"""
        
        print("ANALYZING DEMO OBSERVABILITY DATA")
        print("=" * 50)
        print(f"Demo Period: {self.demo_start_time.strftime('%H:%M:%S')} - {self.demo_end_time.strftime('%H:%M:%S')}")
        print(f"Duration: {int((self.demo_end_time - self.demo_start_time).total_seconds())} seconds")
        print()
        
        start_time_ms = int(self.demo_start_time.timestamp() * 1000)
        end_time_ms = int(self.demo_end_time.timestamp() * 1000)
        
        print("Collecting data from Lambda functions...")
        
        for log_group in self.log_groups:
            print(f"   Scanning {log_group.split('/')[-1]}...")
            
            try:
                # Get customer events
                response = self.logs_client.filter_log_events(
                    logGroupName=log_group,
                    startTime=start_time_ms,
                    endTime=end_time_ms,
                    filterPattern='CUSTOMER_EVENT'
                )
                
                for event in response['events']:
                    self.process_customer_event(event)
                
                # Get error events
                response = self.logs_client.filter_log_events(
                    logGroupName=log_group,
                    startTime=start_time_ms,
                    endTime=end_time_ms,
                    filterPattern='CUSTOMER_ERROR'
                )
                
                for event in response['events']:
                    self.process_error_event(event)
                
                # Get performance metrics
                response = self.logs_client.filter_log_events(
                    logGroupName=log_group,
                    startTime=start_time_ms,
                    endTime=end_time_ms,
                    filterPattern='CUSTOMER_METRIC'
                )
                
                for event in response['events']:
                    self.process_performance_event(event)
                
                # Get system events (subscription changes, etc.)
                response = self.logs_client.filter_log_events(
                    logGroupName=log_group,
                    startTime=start_time_ms,
                    endTime=end_time_ms,
                    filterPattern='SUBSCRIPTION_DISABLED OR SUBSCRIPTION_ENABLED'
                )
                
                for event in response['events']:
                    self.process_system_event(event)
                    
            except Exception as e:
                print(f"   Error scanning {log_group}: {e}")
        
        print(f"Data collection complete!")
        print(f"   {len(self.all_events)} total events")
        print(f"   {len(self.customer_journeys)} unique customers")
        print(f"   {len(self.error_events)} error events")
        print(f"   {len(self.performance_metrics)} performance metrics")
        print(f"   {len(self.system_events)} system events")
    
    def process_customer_event(self, event):
        """Process a customer event"""
        try:
            if 'CUSTOMER_EVENT:' in event['message']:
                json_part = event['message'].split('CUSTOMER_EVENT: ')[1]
                event_data = json.loads(json_part)
                
                event_data['log_timestamp'] = event['timestamp']
                event_data['log_group'] = event.get('logStream', 'unknown')
                
                self.all_events.append(event_data)
                
                customer_id = event_data.get('customer_id', 'unknown')
                self.customer_journeys[customer_id].append(event_data)
                
        except Exception as e:
            pass  # Skip malformed events
    
    def process_error_event(self, event):
        """Process an error event"""
        try:
            if 'CUSTOMER_ERROR:' in event['message']:
                json_part = event['message'].split('CUSTOMER_ERROR: ')[1]
                error_data = json.loads(json_part)
                
                error_data['log_timestamp'] = event['timestamp']
                self.error_events.append(error_data)
                
        except Exception as e:
            pass
    
    def process_performance_event(self, event):
        """Process a performance metric"""
        try:
            if 'CUSTOMER_METRIC:' in event['message']:
                json_part = event['message'].split('CUSTOMER_METRIC: ')[1]
                metric_data = json.loads(json_part)
                
                metric_data['log_timestamp'] = event['timestamp']
                self.performance_metrics.append(metric_data)
                
        except Exception as e:
            pass
    
    def process_system_event(self, event):
        """Process a system event"""
        self.system_events.append({
            'timestamp': event['timestamp'],
            'message': event['message'],
            'log_group': event.get('logStream', 'unknown')
        })
    
    def show_demo_timeline(self):
        """Show chronological timeline of demo events"""
        
        print(f"\nDEMO TIMELINE - CHRONOLOGICAL EVENT FLOW")
        print("=" * 80)
        
        # Combine all events and sort by timestamp
        timeline_events = []
        
        for event in self.all_events:
            timeline_events.append({
                'timestamp': event['log_timestamp'],
                'type': 'customer_event',
                'data': event
            })
        
        for event in self.error_events:
            timeline_events.append({
                'timestamp': event['log_timestamp'],
                'type': 'error_event',
                'data': event
            })
        
        for event in self.system_events:
            timeline_events.append({
                'timestamp': event['timestamp'],
                'type': 'system_event',
                'data': event
            })
        
        # Sort by timestamp
        timeline_events.sort(key=lambda x: x['timestamp'])
        
        print(f"{'Time':<12} {'Type':<15} {'Customer':<25} {'Event':<30} {'Status'}")
        print("-" * 80)
        
        for event in timeline_events[-50:]:  # Show last 50 events
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S.%f')[:-3]
            
            if event['type'] == 'customer_event':
                data = event['data']
                customer_id = data.get('customer_id', 'unknown')[:20]
                event_type = data.get('event_type', 'unknown')[:25]
                status = data.get('status', 'unknown')
                
                # Status icons
                status_icon = 'OK' if status == 'success' else 'ERR' if status == 'error' else 'PROC'
                
                print(f"{timestamp:<12} {'Customer':<15} {customer_id:<25} {event_type:<30} {status_icon}")
                
            elif event['type'] == 'error_event':
                data = event['data']
                customer_id = data.get('customer_id', 'unknown')[:20]
                error_type = data.get('error_type', 'unknown')[:25]
                
                print(f"{timestamp:<12} {'Error':<15} {customer_id:<25} {error_type:<30} ERR")
                
            elif event['type'] == 'system_event':
                message = event['data']['message']
                if 'SUBSCRIPTION_DISABLED' in message:
                    print(f"{timestamp:<12} {'System':<15} {'system':<25} {'subscription_disabled':<30} STOP")
                elif 'SUBSCRIPTION_ENABLED' in message:
                    print(f"{timestamp:<12} {'System':<15} {'system':<25} {'subscription_enabled':<30} START")
    
    def show_customer_journeys(self):
        """Show individual customer journeys"""
        
        print(f"\n👥 CUSTOMER JOURNEYS DURING DEMO")
        print("=" * 60)
        
        # Find customers from demo_5 sequence (ERROR500 prefix)
        demo_customers = {k: v for k, v in self.customer_journeys.items() 
                         if 'ERROR500' in k or 'normal-' in k or 'LIVE-' in k}
        
        if not demo_customers:
            print("No demo customers found in this time period")
            return
        
        for customer_id, events in demo_customers.items():
            print(f"\nCustomer: {customer_id}")
            print("-" * 40)
            
            # Sort events by timestamp
            events.sort(key=lambda x: x.get('log_timestamp', 0))
            
            for event in events:
                timestamp = datetime.fromtimestamp(event['log_timestamp'] / 1000).strftime('%H:%M:%S.%f')[:-3]
                event_type = event.get('event_type', 'unknown')
                status = event.get('status', 'unknown')
                service = event.get('service', 'unknown')
                
                status_icon = 'OK' if status == 'success' else 'ERR' if status == 'error' else 'PROC'
                
                print(f"   {timestamp} {status_icon} {event_type:<25} [{service}]")
                
                # Show additional details for key events
                if event_type == 'demo_500_error_triggered':
                    print(f"      Simulated external service failure")
                elif event_type == 'subscription_disabled':
                    print(f"      System protected itself from cascade failure")
                elif event_type == 'subscription_enabled':
                    print(f"      System recovered and resumed processing")
    
    def show_error_analysis(self):
        """Show error analysis from the demo"""
        
        print(f"\nERROR ANALYSIS")
        print("=" * 40)
        
        if not self.error_events:
            print("No errors detected during demo period")
            return
        
        # Group errors by type
        error_types = Counter(event.get('error_type', 'unknown') for event in self.error_events)
        
        print(f"Error Summary:")
        for error_type, count in error_types.most_common():
            print(f"   {error_type}: {count} occurrences")
        
        print(f"\nError Details:")
        for event in self.error_events[-10:]:  # Last 10 errors
            timestamp = datetime.fromtimestamp(event['log_timestamp'] / 1000).strftime('%H:%M:%S.%f')[:-3]
            customer_id = event.get('customer_id', 'unknown')[:20]
            error_type = event.get('error_type', 'unknown')
            error_message = event.get('error_message', 'No message')[:50]
            
            print(f"   {timestamp} | {customer_id:<20} | {error_type:<20} | {error_message}")
    
    def show_performance_analysis(self):
        """Show performance metrics from the demo"""
        
        print(f"\nPERFORMANCE ANALYSIS")
        print("=" * 40)
        
        if not self.performance_metrics:
            print("No performance metrics found during demo period")
            return
        
        # Group by operation
        operations = defaultdict(list)
        for metric in self.performance_metrics:
            operation = metric.get('operation', 'unknown')
            duration = metric.get('duration_ms', 0)
            operations[operation].append(duration)
        
        print(f"Performance Summary:")
        for operation, durations in operations.items():
            if durations:
                avg_duration = sum(durations) / len(durations)
                max_duration = max(durations)
                min_duration = min(durations)
                count = len(durations)
                
                print(f"   {operation}:")
                print(f"      Count: {count}")
                print(f"      Average: {avg_duration:.2f}ms")
                print(f"      Min: {min_duration:.2f}ms")
                print(f"      Max: {max_duration:.2f}ms")
    
    def show_system_resilience_events(self):
        """Show system resilience events"""
        
        print(f"\nSYSTEM RESILIENCE EVENTS")
        print("=" * 45)
        
        if not self.system_events:
            print("No system resilience events found")
            return
        
        for event in self.system_events:
            timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%H:%M:%S.%f')[:-3]
            message = event['message']
            
            if 'SUBSCRIPTION_DISABLED' in message:
                print(f"   {timestamp} STOP Subscription Disabled (System Protection)")
                if 'UUID' in message:
                    uuid = message.split('UUID: ')[1].split(' ')[0] if 'UUID: ' in message else 'unknown'
                    print(f"      Mapping UUID: {uuid}")
                    
            elif 'SUBSCRIPTION_ENABLED' in message:
                print(f"   {timestamp} START Subscription Enabled (System Recovery)")
                if 'UUID' in message:
                    uuid = message.split('UUID: ')[1].split(' ')[0] if 'UUID: ' in message else 'unknown'
                    print(f"      Mapping UUID: {uuid}")
    
    def show_business_impact_summary(self):
        """Show business impact summary"""
        
        print(f"\n💼 BUSINESS IMPACT SUMMARY")
        print("=" * 45)
        
        # Count successful vs failed transactions
        successful_transactions = len([e for e in self.all_events 
                                     if e.get('event_type') == 'bank_account_setup_completed' 
                                     and e.get('status') == 'success'])
        
        failed_transactions = len([e for e in self.error_events 
                                 if e.get('error_type') == 'external_service_error'])
        
        total_customers = len(self.customer_journeys)
        
        # Calculate system protection events
        protection_events = len([e for e in self.system_events 
                               if 'SUBSCRIPTION_DISABLED' in e['message']])
        
        recovery_events = len([e for e in self.system_events 
                             if 'SUBSCRIPTION_ENABLED' in e['message']])
        
        print(f"Transaction Summary:")
        print(f"   Total Customers: {total_customers}")
        print(f"   Successful Transactions: {successful_transactions}")
        print(f"   Failed Transactions: {failed_transactions}")
        
        print(f"\nSystem Protection:")
        print(f"   Protection Activations: {protection_events}")
        print(f"   Recovery Completions: {recovery_events}")
        
        print(f"\nBusiness Value Demonstrated:")
        if protection_events > 0:
            print(f"   - System automatically protected against cascade failures")
            print(f"   - Customer data preserved during outages")
            print(f"   - Zero manual intervention required")
        
        if recovery_events > 0:
            print(f"   - Automatic recovery when services restored")
            print(f"   - Queued transactions processed successfully")
        
        print(f"   - Complete observability and audit trail")
        print(f"   - Real-time monitoring and alerting")
    
    def generate_demo_report(self):
        """Generate complete demo observability report"""
        
        print(f"\nDEMO OBSERVABILITY REPORT")
        print("=" * 60)
        print(f"This report shows all the observability data that was")
        print(f"captured during your demo_5 sequence demonstration.")
        print(f"Every event, error, and system action was tracked in real-time.")
        print()
        
        # Collect all data
        self.collect_demo_data()
        
        # Show different aspects
        self.show_demo_timeline()
        self.show_customer_journeys()
        self.show_error_analysis()
        self.show_performance_analysis()
        self.show_system_resilience_events()
        self.show_business_impact_summary()
        
        print(f"\nOBSERVABILITY DEMONSTRATION COMPLETE")
        print("=" * 50)
        print("Key Takeaways:")
        print("- Every customer interaction was tracked")
        print("- All errors were detected and classified")
        print("- System protection events were logged")
        print("- Performance metrics were captured")
        print("- Complete audit trail is available")
        print("- Customer support has full visibility")
        print()
        print("This is the power of comprehensive observability!")

def main():
    """Main function"""
    
    print("DEMO OBSERVABILITY DATA ANALYZER")
    print("=" * 50)
    print("This script analyzes all observability data captured")
    print("during your demo_5 sequence demonstration.")
    print()
    
    # Ask for demo timeframe
    print("Demo timeframe options:")
    print("1. Last 15 minutes (default)")
    print("2. Last 30 minutes")
    print("3. Last 60 minutes")
    print("4. Custom time range")
    
    choice = input("\nSelect option (1-4) [1]: ").strip() or "1"
    
    if choice == "1":
        start_time = datetime.utcnow() - timedelta(minutes=15)
    elif choice == "2":
        start_time = datetime.utcnow() - timedelta(minutes=30)
    elif choice == "3":
        start_time = datetime.utcnow() - timedelta(minutes=60)
    elif choice == "4":
        minutes = int(input("Enter minutes to look back: "))
        start_time = datetime.utcnow() - timedelta(minutes=minutes)
    else:
        start_time = datetime.utcnow() - timedelta(minutes=15)
    
    # Create analyzer and generate report
    analyzer = DemoObservabilityAnalyzer(start_time)
    analyzer.generate_demo_report()

if __name__ == "__main__":
    main()