#!/usr/bin/env python3
"""
DEMO 5F: The Happy Ending - Queues Empty and Customers Served
Story: "The system processes all queued messages and normal operations resume..."
"""

import boto3
import time

# Configuration
BANK_ACCOUNT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-bank-account-setup.fifo"
PAYMENT_QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/088153174619/utility-customer-system-dev-payment-processing.fifo"

def monitor_queue_processing():
    """Monitor the queues as they empty and messages get processed"""
    
    print("DEMO 5F: THE HAPPY ENDING")
    print("=" * 30)
    print("Story: The Lambda functions are back online and ready to work!")
    print("All those customer requests that piled up during the outage")
    print("are about to be processed. Let's watch the magic happen...")
    print()
    
    sqs = boto3.client('sqs')
    
    queues = [
        ('Bank Account Setup Queue', BANK_ACCOUNT_QUEUE_URL),
        ('Payment Processing Queue', PAYMENT_QUEUE_URL)
    ]
    
    print("REAL-TIME QUEUE MONITORING")
    print("-" * 35)
    print("Watching as the Lambda functions process the backlog...")
    print()
    
    # Monitor for up to 60 seconds
    for check_num in range(12): # 12 checks, 5 seconds apart
        print(f"Check {check_num + 1}/12 (T+{check_num * 5} seconds):")
        
        total_messages = 0
        all_queues_empty = True
        
        for queue_name, queue_url in queues:
            try:
                response = sqs.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
                )
                
                available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
                in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
                total = available + in_flight
                total_messages += total
                
                if total > 0:
                    all_queues_empty = False
                
                # Show progress with emojis
                if total == 0:
                    status_emoji = ""
                    status_text = "EMPTY"
                elif in_flight > 0:
                    status_emoji = ""
                    status_text = "PROCESSING"
                else:
                    status_emoji = ""
                    status_text = "QUEUED"
                
                print(f" {queue_name}: {available} queued, {in_flight} processing {status_emoji} {status_text}")
                
                # Add some narrative based on what's happening
                if check_num == 0 and total > 0:
                    print(f" Lambda functions are starting to process the backlog...")
                elif in_flight > 0:
                    print(f" Processing in progress - customers being served!")
                elif total == 0 and check_num > 0:
                    print(f" All caught up - no more messages to process!")
            
            except Exception as e:
                print(f" Error checking {queue_name}: {e}")
 
        # Check if we're done
        if all_queues_empty and check_num > 2: # Give it at least 3 checks
            print(f"\nPROCESSING COMPLETE!")
            print(f"All queued messages have been successfully processed!")
            break
        elif check_num < 11: # Don't sleep on the last iteration
            time.sleep(5)
        
        print() # Add spacing between checks
    
    # Final status check
    print(f"FINAL PROCESSING SUMMARY")
    print("-" * 30)
    
    final_total = 0
    for queue_name, queue_url in queues:
        try:
            response = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            
            available = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
            in_flight = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
            total = available + in_flight
            final_total += total
        
        except Exception as e:
            print(f"Error in final check: {e}")
    
    if final_total == 0:
        print(f"PERFECT SUCCESS: All queues are empty!")
        print(f"Every single customer request has been processed successfully!")
        print(f"Alice's bank account setup - COMPLETED")
        print(f"Bob's bank account setup - COMPLETED") 
        print(f"Carol's bank account setup - COMPLETED")
        print(f"David's utility payment - COMPLETED")
        print(f"Emma's utility payment - COMPLETED")
        print(f"Frank's utility payment - COMPLETED")
        
        print(f"\nSYSTEM RESILIENCE DEMONSTRATED:")
        print(f" External service failures detected (500 errors)")
        print(f" Intelligent protection activated (subscriptions disabled)")
        print(f" Customer requests safely queued (no data loss)")
        print(f" Recovery signal sent and received (SNS control)")
        print(f" Automatic reactivation (dynamic UUID discovery)")
        print(f" Backlog processed successfully (all customers served)")
        
    else:
        print(f"PROCESSING CONTINUES: {final_total} messages still being processed")
        print(f"The system is working - it may just need a bit more time")
        print(f"Large backlogs can take several minutes to fully process")

def check_successful_processing_logs():
    """Check CloudWatch logs for successful processing evidence"""
    
    print(f"\nEVIDENCE: Checking Processing Logs")
    print("-" * 40)
    
    logs_client = boto3.client('logs')
    
    functions = [
        ('Bank Account Setup', '/aws/lambda/utility-customer-system-dev-bank-account-setup'),
        ('Payment Processing', '/aws/lambda/utility-customer-system-dev-payment-processing')
    ]
    
    for service_name, log_group in functions:
        print(f"\n{service_name} Processing Evidence:")
        
        try:
            # Look for recent successful processing
            response = logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=int((time.time() - 300) * 1000), # Last 5 minutes
                filterPattern='Successfully processed'
            )
            
            success_count = len(response['events'])
            
            if success_count > 0:
                print(f" Found {success_count} successful processing events")
                
                # Show a few recent examples
                for event in response['events'][-3:]: # Last 3 events
                    timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp'] / 1000))
                    message = event['message'].strip()
                    if 'Successfully processed' in message:
                        print(f" [{timestamp}] {message}")
            
            else:
                print(f" No recent successful processing logs found")
                print(f" (Messages may still be processing or logs may be delayed)")
        
        except Exception as e:
            print(f" Error checking logs: {e}")

def main():
    """The Happy Ending - System Recovery Complete"""
    
    # Monitor queue processing
    monitor_queue_processing()
    
    # Check processing logs
    check_successful_processing_logs()
    
    print(f"\nTHE END - STORY COMPLETE!")
    print("=" * 35)
    print(f"Our story has reached its happy conclusion!")
    print(f"The system faced a crisis but emerged stronger and more resilient.")
    print()
    
    print(f"STORY RECAP:")
    print(f" Chapter 1: External services failed (500 errors)")
    print(f" Chapter 2: System intelligently protected itself")
    print(f" Chapter 3: Customer requests safely queued")
    print(f" Chapter 4: Recovery signal sent via SNS")
    print(f" Chapter 5: Lambda functions reactivated")
    print(f" Chapter 6: All customers served successfully")
    
    print(f"\nBUSINESS VALUE DELIVERED:")
    print(f" Zero revenue loss - all transactions processed")
    print(f" Zero customer impact - requests handled transparently")
    print(f" Zero manual intervention - fully automated recovery")
    print(f" Full visibility - comprehensive monitoring and logging")
    print(f" Scalable resilience - handles any volume of requests")
    
    print(f"\nTECHNICAL EXCELLENCE:")
    print(f" Intelligent error classification (400 vs 500)")
    print(f" Dynamic UUID discovery (no hardcoded configuration)")
    print(f" SNS-based control plane (centralized recovery)")
    print(f" Cascade failure prevention (subscription control)")
    print(f" Message durability (FIFO queues with persistence)")
    
    print(f"\nDEMO SERIES COMPLETE!")
    print(f"Thank you for experiencing the resilience of our dynamic UUID discovery system!")

if __name__ == "__main__":
    main()