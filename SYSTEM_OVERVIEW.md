# FIFO Utility Customer System - Complete Overview

## Architecture Summary

This system implements a robust, FIFO-based message processing architecture for utility customer operations with comprehensive error handling and observability.

### Core Components

1. **Single FIFO SNS Topic** (`transaction-processing.fifo`)
   - Entry point for all transactions
   - Routes messages based on `transaction_type` field
   - Ensures message ordering and deduplication

2. **Two FIFO SQS Queues**
   - `bank-account-setup.fifo` - Receives `transaction_type: "bank_account_setup"`
   - `payment-processing.fifo` - Receives `transaction_type: "payment"`

3. **Two Lambda Functions**
   - Bank Account Setup Lambda - Processes account setup requests
   - Payment Processing Lambda - Processes payment transactions

4. **Subscription Control SNS Topic**
   - Controls Lambda subscription states (start/stop)
   - Separate from main transaction flow

5. **OpenTelemetry Integration**
   - Full observability with metrics, traces, and logs
   - CloudWatch integration for monitoring

## Message Flow

```
Customer Request
       ↓
FIFO SNS Topic (transaction-processing.fifo)
       ↓
Message Filtering by transaction_type
       ↓
┌─────────────────────┬─────────────────────┐
│  Bank Account SQS   │   Payment SQS       │
│  (FIFO)            │   (FIFO)            │
└─────────────────────┴─────────────────────┘
       ↓                       ↓
Bank Account Lambda    Payment Lambda
       ↓                       ↓
Account Validation     Payment Processing
```

## Error Handling Strategy

### 1. Happy Path (Normal Processing)
- Messages processed successfully
- Metrics recorded
- Traces captured

### 2. 400 Errors (Client Errors)
- **Action**: Continue processing other messages
- **Examples**: Invalid account format, insufficient funds
- **Behavior**: Log error, continue subscription
- **Test**: Use customer IDs containing "ERROR400"

### 3. 500 Errors (Server Errors)
- **Action**: Stop SQS subscription until restart signal
- **Examples**: Bank service unavailable, payment gateway down
- **Behavior**: Disable event source mapping, wait for SNS restart signal
- **Test**: Use customer IDs containing "ERROR500"

### 4. Subscription Control
- **Stop**: Lambdas stop processing SQS messages (messages pile up)
- **Start**: Lambdas resume processing accumulated messages
- **Control**: Via separate SNS topic with action commands

## FIFO Features

### Message Ordering
- **MessageGroupId**: Set to `customer_id`
- **Benefit**: All messages for same customer processed in order
- **Use Case**: Ensure account setup before payment processing

### Deduplication
- **MessageDeduplicationId**: Set to unique `message_id`
- **Benefit**: Prevents duplicate processing
- **Use Case**: Network retries don't create duplicate transactions

### Message Filtering
- **Filter Attribute**: `transaction_type`
- **Values**: `"bank_account_setup"` or `"payment"`
- **Benefit**: Single SNS topic routes to multiple queues
- **Use Case**: Centralized entry point with specialized processing

## Testing Scenarios

### 1. Message Routing Test
```bash
cd tests && python3 test_fifo_system.py
```
Verifies messages route to correct queues based on transaction_type.

### 2. Happy Path Test
Send normal messages and verify successful processing.

### 3. Error Scenario Test
- Send ERROR400 messages → Verify continued processing
- Send ERROR500 messages → Verify subscription stops

### 4. Subscription Control Test
- Stop subscriptions → Send messages → Verify queue buildup
- Start subscriptions → Verify queue processing resumes

### 5. FIFO Ordering Test
Send multiple messages for same customer and verify processing order.

## Deployment

### Quick Start
```bash
# Deploy everything
./deploy/deploy.sh

# Test the system
cd tests && python3 test_fifo_system.py
```

### Manual Steps
```bash
# 1. Deploy infrastructure
cd terraform
terraform init
terraform apply

# 2. Test with simple messages
cd tests
python3 send_test_messages.py

# 3. View message examples
python3 message_examples.py
```

## Monitoring & Observability

### CloudWatch Metrics
- **Namespace**: `OTEL/UtilityCustomer/Enhanced`
- **Metrics**: 
  - `messages_processed_total`
  - `processing_duration_seconds`
  - `errors_total`
  - `subscription_status`
  - `queue_depth`

### Lambda Logs
- **Location**: `/aws/lambda/{function-name}`
- **Content**: Processing details, errors, timing

### X-Ray Traces
- **Integration**: Automatic via OpenTelemetry
- **Content**: End-to-end request tracing

## Key Benefits

1. **Reliability**: FIFO ensures message ordering and deduplication
2. **Scalability**: Separate queues allow independent scaling
3. **Resilience**: Error handling prevents system-wide failures
4. **Observability**: Comprehensive monitoring and tracing
5. **Flexibility**: Subscription control allows maintenance windows
6. **Simplicity**: Single entry point with automatic routing

## Production Considerations

1. **Dead Letter Queues**: Configured for failed messages
2. **Retry Logic**: Built into SQS and Lambda integration
3. **Monitoring**: Set up CloudWatch alarms for key metrics
4. **Scaling**: Configure Lambda concurrency limits
5. **Security**: IAM roles with least privilege access
6. **Cost**: Monitor FIFO pricing vs standard queues

## Troubleshooting

### Messages Not Processing
1. Check Lambda logs for errors
2. Verify event source mapping is enabled
3. Check SQS queue visibility timeout
4. Verify IAM permissions

### Wrong Queue Routing
1. Check SNS message attributes
2. Verify subscription filter policies
3. Test message format

### Subscription Control Issues
1. Check subscription control SNS topic
2. Verify Lambda environment variables
3. Check event source mapping UUID configuration

### Performance Issues
1. Monitor CloudWatch metrics
2. Check Lambda duration and memory
3. Verify FIFO queue throughput limits
4. Consider batch size optimization

This system provides a robust foundation for utility customer operations with enterprise-grade reliability, observability, and error handling.