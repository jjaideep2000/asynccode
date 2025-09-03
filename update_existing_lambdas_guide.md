# Update Existing Lambda Functions Guide

## 🎯 Objective
Remove subscription control logic from existing Lambda functions now that we have a centralized Subscription Manager Lambda.

## 📋 Changes Required

### 1. Bank Account Setup Lambda

**File**: `src/lambdas/bank-account/handler.py`

**Remove These Functions:**
- `handle_subscription_control()`
- `handle_500_error()` (subscription disable logic)
- SNS subscription control message handling

**Keep These Functions:**
- `validate_bank_account_message()`
- `setup_bank_account()`
- `call_bank_validation_service()`
- Error handling (but without subscription control)

**Updated Handler Logic:**
```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for bank account setup
    Simplified - no subscription control logic
    """
    
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    try:
        # Handle SQS messages only (no SNS subscription control)
        if 'Records' in event:
            results = []
            
            for record in event['Records']:
                if record.get('eventSource') == 'aws:sqs':
                    # Parse SQS message
                    message_body = json.loads(record['body'])
                    
                    # If message came through SNS->SQS, extract the actual message
                    if 'Message' in message_body:
                        message_body = json.loads(message_body['Message'])
                    
                    # Process the message (business logic only)
                    result = process_bank_account_message(message_body)
                    results.append(result)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'processed': len(results),
                    'results': results
                })
            }
            
        else:
            # Direct invocation or test
            result = process_bank_account_message(event)
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Internal server error'
            })
        }
```

### 2. Payment Processing Lambda

**File**: `src/lambdas/payment/handler.py`

**Remove These Functions:**
- SNS subscription control handling
- `error_handler.handle_subscription_control_message()`
- Subscription disable logic in error handling

**Updated Error Handling:**
```python
def process_payment_message(message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single payment message - simplified error handling"""
    
    try:
        # ... existing business logic ...
        
        return {
            'status': 'success',
            'message_id': message_id,
            'customer_id': customer_id,
            'payment_result': payment_result,
            'processing_time': processing_time
        }
        
    except Exception as e:
        # Simplified error handling - no subscription control
        processing_time = time.time() - start_time
        
        # Log error but don't disable subscriptions
        logger.error(f"Error processing payment: {e}")
        
        # For 500 errors, send notification to SNS for centralized handling
        if is_500_error(e):
            send_500_error_notification(customer_id, str(e))
        
        return {
            'status': 'error',
            'message_id': message_id,
            'customer_id': customer_id,
            'error': str(e),
            'processing_time': processing_time
        }

def send_500_error_notification(customer_id: str, error_message: str):
    """Send 500 error notification for centralized handling"""
    
    try:
        sns_client = boto3.client('sns')
        topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
        
        error_notification = {
            "action": "disable",
            "reason": f"500 error detected: {error_message}",
            "source_service": "payment-processing",
            "customer_id": customer_id,
            "error_type": "500_error",
            "timestamp": datetime.utcnow().isoformat(),
            "operator": "system"
        }
        
        sns_client.publish(
            TopicArn=topic_arn,
            Message=json.dumps(error_notification),
            Subject="500 Error - Request Subscription Disable"
        )
        
        logger.info(f"Sent 500 error notification for customer {customer_id}")
        
    except Exception as e:
        logger.error(f"Failed to send 500 error notification: {e}")

def is_500_error(exception: Exception) -> bool:
    """Determine if error is a 500-type error"""
    error_message = str(exception).lower()
    return any(word in error_message for word in [
        'unavailable', 'gateway', 'service', 'timeout', '500'
    ])
```

### 3. Update Shared Error Handler

**File**: `src/shared/error_handler.py`

**Remove These Methods:**
- `handle_subscription_control_message()`
- `disable_subscription()`
- `enable_subscription()`
- Dynamic UUID discovery for subscription control

**Keep These Methods:**
- `handle_error()` (but simplified)
- Error classification logic
- Logging and monitoring

**Updated Error Handler:**
```python
class ErrorHandler:
    """Simplified error handler without subscription control"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.sns_client = boto3.client('sns')
        self.control_topic_arn = "arn:aws:sns:us-east-2:088153174619:utility-customer-system-dev-subscription-control"
    
    def handle_error(self, error: Exception, message_data: Dict[str, Any], 
                    status_code: int = None) -> Dict[str, Any]:
        """Handle error with centralized notification for 500 errors"""
        
        error_type = self._classify_error(error, status_code)
        
        # For 500 errors, notify centralized subscription manager
        if error_type == 'server_error':
            self._notify_500_error(message_data.get('customer_id', 'unknown'), str(error))
        
        return {
            'error_type': error_type,
            'error_message': str(error),
            'status_code': status_code or 500,
            'service': self.service_name,
            'action': 'logged' if error_type != 'server_error' else 'notification_sent'
        }
    
    def _notify_500_error(self, customer_id: str, error_message: str):
        """Notify centralized subscription manager of 500 error"""
        
        try:
            notification = {
                "action": "disable",
                "reason": f"500 error in {self.service_name}: {error_message}",
                "source_service": self.service_name,
                "customer_id": customer_id,
                "error_type": "500_error",
                "timestamp": datetime.utcnow().isoformat(),
                "operator": "system"
            }
            
            self.sns_client.publish(
                TopicArn=self.control_topic_arn,
                Message=json.dumps(notification),
                Subject=f"500 Error - {self.service_name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to notify subscription manager: {e}")
```

## 🚀 Deployment Steps

### Step 1: Deploy Subscription Manager
```bash
python3 deploy_subscription_manager.py
```

### Step 2: Update Existing Lambda Functions
```bash
# Update bank account Lambda
python3 deploy_updated_bank_account_lambda.py

# Update payment processing Lambda  
python3 deploy_updated_payment_lambda.py
```

### Step 3: Test Integration
```bash
python3 test_centralized_subscription_manager.py
```

### Step 4: Verify End-to-End Flow
```bash
# Run demo to ensure everything works
python3 demo_5a_trigger_500_errors.py
python3 demo_5b_subscriptions_disabled.py
python3 demo_5d_send_resubscribe.py
python3 demo_5e_subscriptions_enabled.py
```

## 📊 Benefits of Centralized Approach

### Before (Distributed):
```
┌─────────────────┐    ┌─────────────────┐
│ Bank Account    │    │ Payment         │
│ Lambda          │    │ Lambda          │
│                 │    │                 │
│ ├─ Business     │    │ ├─ Business     │
│ │  Logic        │    │ │  Logic        │
│ ├─ Error        │    │ ├─ Error        │
│ │  Handling     │    │ │  Handling     │
│ └─ Subscription │    │ └─ Subscription │
│    Control      │    │    Control      │
└─────────────────┘    └─────────────────┘
```

### After (Centralized):
```
┌─────────────────┐    ┌─────────────────┐
│ Bank Account    │    │ Payment         │
│ Lambda          │    │ Lambda          │
│                 │    │                 │
│ ├─ Business     │    │ ├─ Business     │
│ │  Logic        │    │ │  Logic        │
│ └─ Error        │    │ └─ Error        │
│    Handling     │    │    Handling     │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │ SNS Notifications
                     ▼
         ┌─────────────────────────┐
         │ Subscription Manager    │
         │ Lambda                  │
         │                         │
         │ ├─ Centralized Control  │
         │ ├─ Multi-Function Mgmt  │
         │ └─ Status Monitoring    │
         └─────────────────────────┘
```

## ✅ Validation Checklist

- [ ] Subscription Manager Lambda deployed
- [ ] SNS subscription configured
- [ ] Bank Account Lambda updated (subscription logic removed)
- [ ] Payment Lambda updated (subscription logic removed)
- [ ] Error handlers updated to send notifications
- [ ] End-to-end testing completed
- [ ] Demo scenarios working
- [ ] Monitoring and logging verified

## 🔮 Future Enhancements

### Easy Addition of New Lambda Functions:
```json
{
  "MANAGED_FUNCTIONS": [
    {
      "function_name": "utility-customer-system-dev-bank-account-setup",
      "service_name": "bank-account-setup",
      "description": "Bank account setup processing"
    },
    {
      "function_name": "utility-customer-system-dev-payment-processing",
      "service_name": "payment-processing",
      "description": "Payment processing"
    },
    {
      "function_name": "utility-customer-system-dev-notification-service",
      "service_name": "notification-service", 
      "description": "Customer notifications"
    },
    {
      "function_name": "utility-customer-system-dev-billing-service",
      "service_name": "billing-service",
      "description": "Billing and invoicing"
    }
  ]
}
```

This centralized approach provides:
- **Single Responsibility**: Each Lambda focuses on business logic
- **Centralized Control**: One place to manage all subscriptions
- **Easy Scaling**: Add new functions by updating configuration
- **Consistent Behavior**: Uniform subscription management across all services
- **Better Monitoring**: Centralized status and logging