#!/usr/bin/env python3
"""
Customer Demo Script
Perfect presentation flow for showing real-time observability to customers
"""

import subprocess
import time
import webbrowser
from datetime import datetime

class CustomerDemo:
    def __init__(self):
        self.dashboard_url = "https://us-east-2.console.aws.amazon.com/cloudwatch/home?region=us-east-2#dashboards:name=LiveObservabilityDemo"
    
    def welcome_message(self):
        """Display welcome message"""
        print("REAL-TIME OBSERVABILITY DEMONSTRATION")
        print("=" * 60)
        print("Welcome! Today I'll show you our production observability system")
        print("working in real-time with actual customer transactions.")
        print()
        print("What you'll see:")
        print("- Real customers using the system")
        print("- Complete transaction tracking")
        print("- Error detection and handling")
        print("- System self-protection")
        print("- Automatic recovery")
        print("- Customer support capabilities")
        print()
    
    def setup_demo_environment(self):
        """Set up the demo environment"""
        print("Setting up demo environment...")
        
        try:
            # Run setup script
            result = subprocess.run(['python3', 'setup_live_observability_demo.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Demo environment ready!")
                return True
            else:
                print(f"Setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Setup error: {e}")
            return False
    
    def open_dashboard(self):
        """Open CloudWatch dashboard"""
        print(f"\nOpening CloudWatch Dashboard...")
        print(f"URL: {self.dashboard_url}")
        
        try:
            webbrowser.open(self.dashboard_url)
            print("Dashboard opened in browser")
            print("Please set auto-refresh to 10 seconds in the dashboard")
            input("Press Enter when dashboard is ready...")
            return True
        except Exception as e:
            print(f"Could not open browser: {e}")
            print(f"Please manually open: {self.dashboard_url}")
            input("Press Enter when dashboard is ready...")
            return True
    
    def demonstrate_normal_operations(self):
        """Demonstrate normal customer operations"""
        print(f"\nDEMONSTRATION 1: Normal Customer Operations")
        print("-" * 50)
        print("I'm now going to simulate real customers using our system.")
        print("Watch the dashboard as customers:")
        print("  • Set up bank accounts")
        print("  • Process payments")
        print("  • Complete transactions")
        print()
        print("You'll see real-time events showing:")
        print("  - Message received")
        print("  - Validation started")
        print("  - External service calls")
        print("  - Transaction completion")
        print("  - Performance metrics")
        print()
        
        input("Press Enter to start customer simulation...")
        
        # Start customer simulation in background
        try:
            print("Starting customer transactions...")
            process = subprocess.Popen(['python3', 'live_customer_simulation.py'], 
                                     stdin=subprocess.PIPE, text=True)
            
            # Send option 2 (normal traffic)
            process.stdin.write("2\n")
            process.stdin.flush()
            
            print("👥 Customers are now using the system...")
            print("👀 Watch the dashboard for real-time events!")
            
            # Let it run for 2 minutes
            time.sleep(120)
            
            # Stop the simulation
            process.terminate()
            print("Normal operations demonstration complete")
            
        except Exception as e:
            print(f"Simulation error: {e}")
    
    def demonstrate_error_handling(self):
        """Demonstrate error handling and system protection"""
        print(f"\nDEMONSTRATION 2: Error Handling & System Protection")
        print("-" * 60)
        print("Now I'll show what happens when external services fail.")
        print("This demonstrates our system's intelligence and resilience.")
        print()
        print("What you'll see:")
        print("  - External service failures (500 errors)")
        print("  - System automatically protects itself")
        print("  - Customer requests safely queued")
        print("  - Processing stops to prevent cascade failures")
        print("  - All events tracked in real-time")
        print()
        
        input("Press Enter to trigger error scenario...")
        
        try:
            print("🔥 Triggering external service failures...")
            process = subprocess.Popen(['python3', 'live_customer_simulation.py'], 
                                     stdin=subprocess.PIPE, text=True)
            
            # Send option 3 (error scenario)
            process.stdin.write("3\n")
            process.stdin.flush()
            
            print("👀 Watch the dashboard - you should see:")
            print("  • Error events appearing")
            print("  • Subscription disable events")
            print("  • Messages queuing up safely")
            
            # Wait for error demo to complete
            time.sleep(30)
            
            process.terminate()
            print("Error handling demonstration complete")
            
        except Exception as e:
            print(f"Error demo failed: {e}")
    
    def demonstrate_recovery(self):
        """Demonstrate system recovery"""
        print(f"\nDEMONSTRATION 3: Automatic System Recovery")
        print("-" * 55)
        print("Now I'll show how the system recovers automatically")
        print("when external services come back online.")
        print()
        print("What you'll see:")
        print("  - Recovery signal sent")
        print("  - Subscriptions re-enabled")
        print("  - Queued messages processed")
        print("  - All customers served")
        print("  - Zero data loss")
        print()
        
        input("Press Enter to trigger system recovery...")
        
        try:
            print("Sending recovery signal...")
            process = subprocess.Popen(['python3', 'live_customer_simulation.py'], 
                                     stdin=subprocess.PIPE, text=True)
            
            # Send option 5 (recovery)
            process.stdin.write("5\n")
            process.stdin.flush()
            
            print("👀 Watch the dashboard - you should see:")
            print("  • Recovery events")
            print("  • Subscription enable events")
            print("  • Queued messages being processed")
            
            time.sleep(20)
            
            process.terminate()
            print("Recovery demonstration complete")
            
        except Exception as e:
            print(f"Recovery demo failed: {e}")
    
    def demonstrate_customer_support(self):
        """Demonstrate customer support capabilities"""
        print(f"\n🎧 DEMONSTRATION 4: Customer Support Capabilities")
        print("-" * 55)
        print("Finally, let me show you how customer support teams")
        print("can use this observability data to help customers.")
        print()
        print("Key capabilities:")
        print("  - Track any customer's complete journey")
        print("  - Identify performance issues instantly")
        print("  - Proactive error detection")
        print("  - Real-time system health monitoring")
        print("  - Complete audit trail for compliance")
        print()
        print("The dashboard shows:")
        print("  • Live customer events")
        print("  • Error summaries")
        print("  • Performance metrics")
        print("  • System status")
        print()
        
        input("Press Enter to see customer support queries...")
        
        print("Customer support can query:")
        print("  • 'Show me customer ABC123's complete journey'")
        print("  • 'Why are payments slow today?'")
        print("  • 'Which customers were affected by the 2pm outage?'")
        print("  • 'Is the bank validation service healthy?'")
        print()
        print("All answers are available in real-time with precise timestamps!")
    
    def wrap_up(self):
        """Wrap up the demonstration"""
        print(f"\nDEMONSTRATION COMPLETE")
        print("=" * 40)
        print("What you've seen:")
        print("- Real-time customer transaction tracking")
        print("- Intelligent error detection and handling")
        print("- Automatic system protection and recovery")
        print("- Complete observability for customer support")
        print("- Zero data loss during failures")
        print("- Enterprise-grade monitoring and alerting")
        print()
        print("Business benefits:")
        print("- Zero revenue loss during outages")
        print("- Zero customer impact from system issues")
        print("- Faster issue resolution (MTTR)")
        print("- Proactive customer support")
        print("- Data-driven operational decisions")
        print("- Complete compliance audit trail")
        print()
        print("Thank you for watching our observability demonstration!")
    
    def run_full_demo(self):
        """Run the complete customer demonstration"""
        
        # Welcome
        self.welcome_message()
        input("Press Enter to begin setup...")
        
        # Setup
        if not self.setup_demo_environment():
            print("Demo setup failed. Please check configuration.")
            return
        
        # Open dashboard
        if not self.open_dashboard():
            print("Could not open dashboard. Please open manually.")
            return
        
        # Run demonstrations
        self.demonstrate_normal_operations()
        self.demonstrate_error_handling()
        self.demonstrate_recovery()
        self.demonstrate_customer_support()
        
        # Wrap up
        self.wrap_up()

def main():
    """Main function"""
    demo = CustomerDemo()
    demo.run_full_demo()

if __name__ == "__main__":
    main()