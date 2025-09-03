#!/usr/bin/env python3
"""
Live Customer Simulation for Real-Time Observability Demo
Simulates real customers using the system while you watch CloudWatch dashboard
"""

import json
import boto3
import time
import random
from datetime import datetime
from threading import Thread

# Configuration
TRANSACTION_PROCESSING_TOPIC_ARN = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-transaction-processing.fifo"

class LiveCustomerSimulator:
    def __init__(self):
        self.sns_client = boto3.client('sns')
        self.running = False
        self.customer_counter = 0
        
        # Realistic customer data
        self.customer_names = [
            "Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson",
            "Emma Brown", "Frank Miller", "Grace Lee", "Henry Taylor",
            "Ivy Chen", "Jack Anderson", "Kate Martinez", "Liam Garcia"
        ]
        
        self.banks = [
            "Chase Bank", "Wells Fargo", "Bank of America", "Citibank",
            "US Bank", "PNC Bank", "Capital One", "TD Bank"
        ]
    
    def generate_realistic_customer(self, scenario_type="success"):
        """Generate realistic customer data"""
        self.customer_counter += 1
        
        name = random.choice(self.customer_names)
        bank = random.choice(self.banks)
        
        # Create customer ID based on scenario
        if scenario_type == "500_error":
            customer_id = f"ERROR500-{name.replace(' ', '')}-{int(time.time())}-{self.customer_counter}"
        elif scenario_type == "400_error":
            customer_id = f"ERROR400-{name.replace(' ', '')}-{int(time.time())}-{self.customer_counter}"
        else:
            customer_id = f"LIVE-{name.replace(' ', '')}-{int(time.time())}-{self.customer_counter}"
        
        return {
            'customer_id': customer_id,
            'name': name,
            'bank': bank,
            'routing_number': f"{random.randint(100000000, 999999999)}",
            'account_number': f"{random.randint(1000000000, 9999999999)}",
            'amount': round(random.uniform(50.00, 500.00), 2)
        }
    
    def send_bank_account_setup(self, customer_data, announce=True):
        """Send bank account setup request"""
        
        if announce:
            print(f"{customer_data['name']} setting up {customer_data['bank']} account...")
        
        message = {
            'customer_id': customer_data['customer_id'],
            'routing_number': customer_data['routing_number'],
            'account_number': customer_data['account_number'],
            'account_type': 'checking',
            'bank_name': customer_data['bank'],
            'message_id': f"live-bank-{int(time.time())}-{self.customer_counter}",
            'message_group_id': customer_data['customer_id'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            response = self.sns_client.publish(
                TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
                Message=json.dumps(message),
                Subject=f"Live Demo: Bank Account Setup - {customer_data['name']}",
                MessageAttributes={
                    'transaction_type': {
                        'DataType': 'String',
                        'StringValue': 'bank_account_setup'
                    },
                    'customer_id': {
                        'DataType': 'String',
                        'StringValue': customer_data['customer_id']
                    },
                    'message_group_id': {
                        'DataType': 'String',
                        'StringValue': customer_data['customer_id']
                    },
                    'live_demo': {
                        'DataType': 'String',
                        'StringValue': 'true'
                    }
                },
                MessageGroupId=customer_data['customer_id'],
                MessageDeduplicationId=f"live-bank-{customer_data['customer_id']}-{int(time.time())}"
            )
            
            if announce:
                print(f"   Request sent (Message ID: {response['MessageId'][:8]}...)")
            
            return True
            
        except Exception as e:
            if announce:
                print(f"   Failed: {e}")
            return False
    
    def send_payment_request(self, customer_data, announce=True):
        """Send payment processing request"""
        
        if announce:
            print(f"💳 {customer_data['name']} paying ${customer_data['amount']} utility bill...")
        
        message = {
            'customer_id': customer_data['customer_id'],
            'amount': customer_data['amount'],
            'payment_method': 'bank_account',
            'currency': 'USD',
            'description': f'Utility bill payment for {customer_data["name"]}',
            'message_id': f"live-payment-{int(time.time())}-{self.customer_counter}",
            'message_group_id': customer_data['customer_id'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            response = self.sns_client.publish(
                TopicArn=TRANSACTION_PROCESSING_TOPIC_ARN,
                Message=json.dumps(message),
                Subject=f"Live Demo: Payment - {customer_data['name']}",
                MessageAttributes={
                    'transaction_type': {
                        'DataType': 'String',
                        'StringValue': 'payment'
                    },
                    'customer_id': {
                        'DataType': 'String',
                        'StringValue': customer_data['customer_id']
                    },
                    'message_group_id': {
                        'DataType': 'String',
                        'StringValue': customer_data['customer_id']
                    },
                    'live_demo': {
                        'DataType': 'String',
                        'StringValue': 'true'
                    }
                },
                MessageGroupId=customer_data['customer_id'],
                MessageDeduplicationId=f"live-payment-{customer_data['customer_id']}-{int(time.time())}"
            )
            
            if announce:
                print(f"   Payment sent (Message ID: {response['MessageId'][:8]}...)")
            
            return True
            
        except Exception as e:
            if announce:
                print(f"   Failed: {e}")
            return False
    
    def simulate_normal_traffic(self, duration_seconds=300):
        """Simulate normal customer traffic"""
        
        print(f"Starting normal customer traffic simulation for {duration_seconds} seconds...")
        print("   (Watch the CloudWatch dashboard for real-time events)")
        
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds and self.running:
            # Generate random customer activity
            activity_type = random.choices(
                ['bank_account', 'payment', 'both'],
                weights=[30, 40, 30],
                k=1
            )[0]
            
            customer = self.generate_realistic_customer()
            
            if activity_type == 'bank_account':
                self.send_bank_account_setup(customer)
            elif activity_type == 'payment':
                self.send_payment_request(customer)
            else:  # both
                self.send_bank_account_setup(customer)
                time.sleep(1)
                self.send_payment_request(customer)
            
            # Random delay between customers (2-8 seconds)
            delay = random.uniform(2, 8)
            time.sleep(delay)
        
        print(f"Normal traffic simulation completed")
    
    def simulate_error_scenario(self):
        """Simulate error scenarios for demonstration"""
        
        print(f"\nDEMONSTRATING ERROR HANDLING")
        print("   Triggering 500 errors to show system protection...")
        
        # Send a few 500 error requests
        for i in range(3):
            customer = self.generate_realistic_customer("500_error")
            print(f"🔥 Triggering 500 error with {customer['name']}...")
            self.send_bank_account_setup(customer)
            time.sleep(2)
        
        print("   Wait 10 seconds and watch the dashboard...")
        print("   You should see:")
        print("     - Error events appear")
        print("     - Subscription disable events")
        print("     - Messages queuing up")
        
        time.sleep(10)
        
        print(f"\nDEMONSTRATING RECOVERY")
        print("   Sending recovery signal...")
        
        # Send recovery signal
        sns_client = boto3.client('sns')
        control_topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
        
        recovery_message = {
            'action': 'enable',
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'live_demo_recovery',
            'reason': 'demonstrating_recovery'
        }
        
        try:
            response = sns_client.publish(
                TopicArn=control_topic_arn,
                Message=json.dumps(recovery_message),
                Subject='Live Demo: System Recovery'
            )
            print(f"   Recovery signal sent")
            
            print("   Wait 15 seconds and watch the dashboard...")
            print("   You should see:")
            print("     - Subscription enable events")
            print("     - Queued messages being processed")
            print("     - System back to normal")
            
            time.sleep(15)
            
        except Exception as e:
            print(f"   Recovery failed: {e}")
    
    def start_continuous_simulation(self):
        """Start continuous customer simulation"""
        
        self.running = True
        
        print(f"LIVE OBSERVABILITY DEMO STARTED")
        print("=" * 50)
        print("Open CloudWatch Dashboard: https://us-east-2.console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=LiveObservabilityDemo")
        print("Set dashboard auto-refresh to 10 seconds")
        print("Watch real-time events as customers use the system")
        print()
        print("Press Ctrl+C to stop the simulation")
        print()
        
        try:
            # Phase 1: Normal traffic (2 minutes)
            print("PHASE 1: Normal Customer Traffic (2 minutes)")
            self.simulate_normal_traffic(120)
            
            # Phase 2: Error demonstration
            print("\nPHASE 2: Error Handling Demonstration")
            self.simulate_error_scenario()
            
            # Phase 3: More normal traffic
            print("\nPHASE 3: Resumed Normal Traffic")
            self.simulate_normal_traffic(180)
            
        except KeyboardInterrupt:
            print(f"\nSimulation stopped by user")
        finally:
            self.running = False
            print(f"\nLive observability demo completed!")
            print("Check the CloudWatch dashboard for the complete event history")

def interactive_demo_menu():
    """Interactive menu for different demo scenarios"""
    
    simulator = LiveCustomerSimulator()
    
    while True:
        print(f"\nLIVE OBSERVABILITY DEMO MENU")
        print("=" * 40)
        print("1. Full Automated Demo (5 minutes)")
        print("2. Normal Traffic Only (continuous)")
        print("3. Error Scenario Demo")
        print("4. Single Customer Transaction")
        print("5. System Recovery Demo")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            simulator.start_continuous_simulation()
        elif choice == "2":
            print("Starting continuous normal traffic...")
            print("Press Ctrl+C to stop")
            try:
                simulator.running = True
                simulator.simulate_normal_traffic(999999)  # Very long duration
            except KeyboardInterrupt:
                print("\nStopped by user")
        elif choice == "3":
            simulator.simulate_error_scenario()
        elif choice == "4":
            customer = simulator.generate_realistic_customer()
            print(f"Sending transaction for {customer['name']}...")
            simulator.send_bank_account_setup(customer)
        elif choice == "5":
            # Just send recovery signal
            sns_client = boto3.client('sns')
            control_topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
            recovery_message = {
                'action': 'enable',
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'manual_recovery_demo'
            }
            response = sns_client.publish(
                TopicArn=control_topic_arn,
                Message=json.dumps(recovery_message),
                Subject='Manual Recovery Demo'
            )
            print("Recovery signal sent")
        elif choice == "6":
            print("Demo ended")
            break
        else:
            print("Invalid choice, please try again")

if __name__ == "__main__":
    interactive_demo_menu()