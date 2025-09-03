#!/usr/bin/env python3
"""
Test script to verify dynamic UUID discovery functionality
"""

import sys
import os
import json
import logging

# Add the shared module to path
sys.path.append('src/shared')

from error_handler import create_error_handler, SubscriptionManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_uuid_discovery():
 """Test the UUID discovery functionality"""
 
 print("🧪 Testing Dynamic UUID Discovery")
 print("=" * 50)
 
 # Test services
 services = ["bank-account-setup", "payment-processing"]
 
 for service_name in services:
 print(f"\nTesting service: {service_name}")
 print("-" * 30)
 
 try:
 # Create error handler (this will trigger UUID discovery)
 error_handler = create_error_handler(service_name)
 
 if error_handler.subscription_manager:
 uuid = error_handler.subscription_manager.event_source_mapping_uuid
 function_name = error_handler.subscription_manager.function_name
 
 print(f"Function Name: {function_name}")
 print(f"Discovered UUID: {uuid}")
 
 if uuid:
 print("UUID discovery successful")
 
 # Test getting subscription status
 try:
 status = error_handler.subscription_manager.get_subscription_status()
 print(f"Current Status: {'Enabled' if status else 'Disabled'}")
 except Exception as e:
 print(f"Could not get status: {e}")
 
 else:
 print("UUID discovery failed")
 else:
 print("No subscription manager created")
 
 except Exception as e:
 print(f"Error testing {service_name}: {e}")
 
 print("\n" + "=" * 50)
 print("UUID Discovery Test Complete")

def test_subscription_manager_directly():
 """Test SubscriptionManager directly"""
 
 print("\nTesting SubscriptionManager Directly")
 print("=" * 50)
 
 function_names = [
 "utility-customer-system-dev-bank-account-setup",
 "utility-customer-system-dev-payment-processing"
 ]
 
 for function_name in function_names:
 print(f"\nTesting function: {function_name}")
 print("-" * 40)
 
 try:
 # Create subscription manager without UUID (will auto-discover)
 manager = SubscriptionManager(function_name)
 
 print(f"Function: {manager.function_name}")
 print(f"UUID: {manager.event_source_mapping_uuid}")
 
 if manager.event_source_mapping_uuid:
 print("Direct UUID discovery successful")
 else:
 print("Direct UUID discovery failed")
 
 except Exception as e:
 print(f"Error: {e}")

if __name__ == "__main__":
 print("Starting UUID Discovery Tests")
 
 test_uuid_discovery()
 test_subscription_manager_directly()
 
 print("\nAll tests completed!")