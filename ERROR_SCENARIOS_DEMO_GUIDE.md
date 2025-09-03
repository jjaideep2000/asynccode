# Error Scenarios Demo Guide

## 🎯 Overview
This guide provides step-by-step commands to demonstrate 400 and 500 error handling scenarios with dynamic UUID discovery.

## 📋 Prerequisites
- Ensure you're in the project root directory
- AWS credentials are configured
- All Lambda functions are deployed and subscriptions are enabled

---

## 🚨 Demo 3: 400 Error Scenario (Continue Processing)

### Scenario Description:
- Send bank account message that triggers 400 error
- Send normal bank account message that processes successfully  
- Confirm 400 error was handled correctly (continue processing)
- Verify subscription remains enabled

### Command:
```bash
python3 demo_3_400_error_scenario.py
```

### Expected Flow:
1. **400 Error Message**: Sent with `ERROR400` in customer ID
2. **Success Message**: Normal message sent immediately after
3. **Processing**: Both messages processed (400 error doesn't stop processing)
4. **Verification**: Logs show 400 error handled, success message processed
5. **Subscription**: Remains enabled (400 errors don't disable subscriptions)

### Expected Output:
```
🚀 CLIENT DEMO - 400 Error Scenario
🎯 Demonstrating 400 error handling (continue processing)
============================================================

🚨 STEP 1: Sending Bank Account Message (400 Error)
--------------------------------------------------
📤 Sending message that will trigger 400 error:
   Customer ID: ERROR400-demo-1756512345 (contains ERROR400)
   Expected: Invalid account number format error
✅ 400 Error message sent successfully!

✅ STEP 2: Sending Normal Bank Account Message (Success)
--------------------------------------------------
📤 Sending normal message:
   Customer ID: success-demo-1756512346
   Expected: Successful processing
✅ Success message sent successfully!

⏳ STEP 3: Waiting for Lambda Processing...
----------------------------------------
📊 Queue Status After Processing:
   - Messages Available: 0
   - Messages In-Flight: 0
✅ All messages processed (both 400 error and success)

🔍 STEP 4: Confirming 400 Error Processing
-----------------------------------------
✅ Found 400 error log:
   [16:45:23] Error processing message: {'error_type': 'client_error'...}
✅ Confirmed: 400 error handled correctly (continuing processing)

🔍 STEP 5: Confirming Success Processing
--------------------------------------
✅ Found success log:
   [16:45:24] Successfully processed bank account setup: VAL-1756512346-1234

📊 STEP 6: Verifying Subscription Status
--------------------------------------
📊 Bank Account Subscription: Enabled (✅)
✅ CORRECT: Subscription remains enabled after 400 error

🎉 DEMO 3 COMPLETE!
```

### Key Points to Highlight:
- ✅ **400 errors are client errors** - system continues processing
- ✅ **Subscriptions remain active** - no service disruption
- ✅ **Subsequent messages process normally** - no impact on other transactions
- ✅ **Error logging and monitoring** - full visibility into error handling

---

## 🔥 Demo 4: 500 Error Scenario (Subscription Control)

### Scenario Description:
- Send messages that trigger 500 errors (bank account + payment)
- Send normal messages that pile up in queues
- Confirm subscriptions are disabled and messages pile up
- Send resubscribe message via SNS
- Confirm Lambda functions resubscribe and process messages
- Verify queues are emptied

### Command:
```bash
python3 demo_4_500_error_scenario.py
```

### Expected Flow:
1. **500 Error Messages**: Sent to both services with `ERROR500` in customer ID
2. **Subscription Disable**: Lambda functions disable their own subscriptions
3. **Message Pileup**: Normal messages sent but pile up in queues (not processed)
4. **SNS Control**: Resubscribe message sent via SNS topic
5. **Resubscription**: Lambda functions re-enable their subscriptions
6. **Processing Resume**: Piled up messages get processed, queues empty

### Expected Output:
```
🚀 CLIENT DEMO - 500 Error Scenario
🎯 Demonstrating 500 error handling (subscription control)
=============================================================

🚨 STEP 1: Sending Messages to Trigger 500 Errors
------------------------------------------------
📤 Sending Bank Account 500 Error Message:
   Customer ID: ERROR500-bank-demo-1756512400 (contains ERROR500)
   Expected: Bank validation service unavailable
   ✅ Bank Account 500 error message sent

📤 Sending Payment 500 Error Message:
   Customer ID: ERROR500-payment-demo-1756512401 (contains ERROR500)
   Expected: Payment gateway unavailable
   ✅ Payment 500 error message sent

⏳ STEP 2: Waiting for 500 Error Processing & Subscription Disable
----------------------------------------------------------------
📊 Subscription Status After 500 Errors:
   Bank Account: Disabled (❌)
   Payment: Disabled (❌)
✅ SUCCESS: 2 subscription(s) disabled by 500 errors

📤 STEP 3: Sending Normal Messages (Should Pile Up)
------------------------------------------------
📤 Sending 3 bank account messages and 3 payment messages...
   ✅ Bank message 1 sent: normal-bank-1-1756512415
   ✅ Bank message 2 sent: normal-bank-2-1756512415
   ✅ Bank message 3 sent: normal-bank-3-1756512415
   ✅ Payment message 1 sent: normal-payment-1-1756512415
   ✅ Payment message 2 sent: normal-payment-2-1756512415
   ✅ Payment message 3 sent: normal-payment-3-1756512415

📊 STEP 4: Confirming Messages Are Piling Up
-------------------------------------------
📊 Bank Account Queue:
   - Available: 3
   - In-Flight: 0
   - Total: 3
📊 Payment Queue:
   - Available: 3
   - In-Flight: 0
   - Total: 3
✅ SUCCESS: 6 messages piled up in queues
   (Subscriptions disabled - messages not being processed)

📢 STEP 5: Sending Resubscribe Message on SNS Topic
------------------------------------------------
📢 Sending resubscribe (enable) message:
   Action: enable
   Topic: Subscription Control
✅ Resubscribe message sent successfully!

⏳ STEP 6: Waiting for Lambda Functions to Resubscribe
----------------------------------------------------
📊 Subscription Status After Resubscribe:
   Bank Account: Enabled (✅)
   Payment: Enabled (✅)
✅ SUCCESS: 2 subscription(s) re-enabled

📊 STEP 7: Confirming Message Processing & Queue Emptying
-------------------------------------------------------
⏰ Check 1/6 (after 0 seconds):
   Bank Account: 3 available, 0 in-flight
   Payment: 3 available, 0 in-flight

⏰ Check 2/6 (after 5 seconds):
   Bank Account: 0 available, 2 in-flight
   Payment: 0 available, 1 in-flight

⏰ Check 3/6 (after 10 seconds):
   Bank Account: 0 available, 0 in-flight
   Payment: 0 available, 0 in-flight
✅ SUCCESS: All queues empty - messages processed!

🎉 DEMO 4 COMPLETE!
```

### Key Points to Highlight:
- ✅ **500 errors disable subscriptions** - prevents cascade failures
- ✅ **Messages pile up safely** - no message loss during outages
- ✅ **SNS control mechanism** - centralized recovery control
- ✅ **Automatic resubscription** - Lambda functions respond to SNS messages
- ✅ **Processing resumes** - piled up messages get processed after recovery
- ✅ **Dynamic UUID discovery** - enables subscription control without hardcoded config

---

## 🔧 Preparation Commands

### Before Running Demos:

1. **Check System Status:**
```bash
python3 demo_check_system_status.py
```

2. **Enable Subscriptions (if needed):**
```bash
python3 demo_enable_subscriptions.py
```

### After Demo 4 (500 Error Scenario):
The demo automatically re-enables subscriptions, but you can manually enable them if needed:
```bash
python3 demo_enable_subscriptions.py
```

---

## 📊 Demo Sequence for Client Presentation

### Recommended Order:
1. **System Status Check** - Show healthy system
2. **Success Scenarios** (Demos 1 & 2) - Show normal operation
3. **400 Error Scenario** (Demo 3) - Show error handling without disruption
4. **500 Error Scenario** (Demo 4) - Show resilience and recovery

### Complete Demo Sequence:
```bash
# 1. Check system status
python3 demo_check_system_status.py

# 2. Enable subscriptions (if needed)
python3 demo_enable_subscriptions.py

# 3. Success scenarios
python3 demo_1_bank_account_success.py
python3 demo_2_payment_success.py

# 4. Error scenarios
python3 demo_3_400_error_scenario.py
python3 demo_4_500_error_scenario.py
```

---

## 🎯 Client Value Proposition

### Error Handling Benefits:
1. **Intelligent Error Classification**: 400 vs 500 errors handled differently
2. **Service Resilience**: 500 errors don't cause cascade failures
3. **No Message Loss**: Messages safely queued during outages
4. **Centralized Recovery**: SNS-based control for service recovery
5. **Dynamic Configuration**: No hardcoded UUIDs, self-discovering system
6. **Comprehensive Monitoring**: Full visibility into error handling and recovery

### Business Impact:
- **High Availability**: System remains operational during partial failures
- **Data Integrity**: No transaction loss during error conditions
- **Operational Efficiency**: Automated recovery reduces manual intervention
- **Scalability**: Error handling scales with message volume
- **Maintainability**: Dynamic configuration reduces operational overhead

The system demonstrates enterprise-grade error handling with intelligent failure modes and automated recovery capabilities.