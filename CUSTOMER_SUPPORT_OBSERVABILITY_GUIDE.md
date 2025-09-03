# Customer Support Observability Guide

## Overview
This guide shows customer support teams how to track and troubleshoot customer bank account setup and payment processing using our comprehensive observability system.

## Quick Customer Lookup

### 1. Find Customer Journey by Customer ID
```
CloudWatch Logs Query:
SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'
| fields @timestamp, @message
| filter @message like /CUSTOMER_EVENT/ and @message like /CUSTOMER_ID_HERE/
| sort @timestamp desc
```

### 2. Track Complete Customer Journey
```
CloudWatch Logs Query:
SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'
| fields @timestamp, customer_id, event_type, status, trace_id
| filter @message like /CUSTOMER_EVENT/
| parse @message /CUSTOMER_EVENT: (?<event_json>.*)/
| parse event_json /"customer_id":\s*"(?<customer_id>[^"]*)"/
| parse event_json /"event_type":\s*"(?<event_type>[^"]*)"/
| parse event_json /"status":\s*"(?<status>[^"]*)"/
| parse event_json /"trace_id":\s*"(?<trace_id>[^"]*)"/
| filter customer_id = "CUSTOMER_ID_HERE"
| sort @timestamp asc
```

## Customer Journey Stages

### Stage 1: Message Received
**Event Type:** `message_received`
- **What it means:** Customer's bank account setup request was received from SQS
- **Key fields:** `source`, `queue_name`, `message_size`, `lambda_request_id`
- **Normal status:** `processing`

### Stage 2: Validation Started
**Event Type:** `validation_started`
- **What it means:** System started validating customer's bank account information
- **Key fields:** `validation_type`
- **Normal status:** `processing`

### Stage 3: Validation Completed/Failed
**Event Type:** `validation_completed` or `validation_failed`
- **What it means:** Bank account information validation finished
- **Key fields:** `validation_checks_passed`, `missing_fields` (if failed)
- **Normal status:** `success` or `error`

### Stage 4: Bank Setup Started
**Event Type:** `bank_setup_started`
- **What it means:** External bank validation service call initiated
- **Key fields:** `routing_number` (masked), `account_number` (masked)
- **Normal status:** `processing`

### Stage 5: External Validation
**Event Type:** `external_validation_completed`
- **What it means:** Bank validation service responded
- **Key fields:** `service`, `duration_ms`, `validation_score`
- **Normal status:** `success` or `error`

### Stage 6: Account Created
**Event Type:** `account_created`
- **What it means:** Bank account successfully set up in our system
- **Key fields:** `account_id`, `account_type`, `status`
- **Normal status:** `success`

### Stage 7: Process Completed
**Event Type:** `bank_account_setup_completed`
- **What it means:** Entire bank account setup process finished
- **Key fields:** `account_id`, `processing_duration_ms`, `validation_checks_passed`
- **Normal status:** `success`

## Common Issues and Troubleshooting

### Issue 1: Customer Says "My Bank Account Setup is Stuck"

**Step 1:** Find the customer's latest events
```
CloudWatch Query:
SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'
| filter @message like /CUSTOMER_EVENT/ and @message like /CUSTOMER_ID/
| sort @timestamp desc
| limit 10
```

**Step 2:** Check the last event status
- If last event is `message_received` → Check if Lambda is processing
- If last event is `validation_started` → Check for validation errors
- If last event is `bank_setup_started` → Check external service status

### Issue 2: Customer Reports Error During Setup

**Step 1:** Find customer errors
```
CloudWatch Query:
SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'
| filter @message like /CUSTOMER_ERROR/ and @message like /CUSTOMER_ID/
| sort @timestamp desc
```

**Step 2:** Classify the error
- `validation_error` → Invalid bank account information provided
- `external_service_error` → Bank validation service is down (500 error)
- `timeout_error` → External service took too long to respond
- `system_error` → Internal system issue

### Issue 3: Performance Issues

**Step 1:** Check processing duration
```
CloudWatch Query:
SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'
| filter @message like /CUSTOMER_METRIC/
| parse @message /CUSTOMER_METRIC: (?<metric_json>.*)/
| parse metric_json /"duration_ms":\s*(?<duration_ms>[0-9.]+)/
| parse metric_json /"customer_id":\s*"(?<customer_id>[^"]*)"/
| filter customer_id = "CUSTOMER_ID"
| sort @timestamp desc
```

**Normal Processing Times:**
- Total bank account setup: 200-500ms
- Validation: 50-100ms
- External bank validation: 100-200ms
- Account creation: 50-100ms

## Error Response Templates

### Validation Error Response
```
"We found an issue with the bank account information you provided. 
Please verify your routing number and account number are correct and try again."
```

### External Service Error Response
```
"We're experiencing temporary issues with our bank validation service. 
Your request has been queued and will be processed automatically once service is restored."
```

### System Error Response
```
"We encountered a technical issue processing your bank account setup. 
Our technical team has been notified. Please try again in a few minutes."
```

## Escalation Criteria

### Escalate to Engineering if:
1. **High Error Rate:** More than 10% of customers experiencing errors in last hour
2. **Performance Degradation:** Average processing time > 1000ms
3. **External Service Issues:** Bank validation service errors > 5% in last 30 minutes
4. **System Errors:** Any `system_error` type errors

### Escalation Information to Provide:
1. **Customer ID(s)** affected
2. **Time range** of the issue
3. **Error type** and frequency
4. **Trace ID(s)** for specific customer journeys
5. **CloudWatch log group** and relevant queries used

## Dashboard Access

### Customer Support Dashboard
- **URL:** CloudWatch Dashboard → "Payment System Customer Support"
- **Key Widgets:**
  - Customer Events (real-time)
  - Error Summary
  - Performance Metrics
  - Journey Tracking

### Real-time Monitoring
```
CloudWatch Live Tail:
aws logs tail /aws/lambda/utility-customer-system-dev-bank-account-setup --follow
```

## Advanced Queries

### Find All Customers with Errors in Last Hour
```
SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'
| filter @message like /CUSTOMER_ERROR/ and @timestamp > (now() - 1h)
| parse @message /CUSTOMER_ERROR: (?<error_json>.*)/
| parse error_json /"customer_id":\s*"(?<customer_id>[^"]*)"/
| parse error_json /"error_type":\s*"(?<error_type>[^"]*)"/
| stats count() by customer_id, error_type
| sort count desc
```

### Performance Analysis by Time Period
```
SOURCE '/aws/lambda/utility-customer-system-dev-bank-account-setup'
| filter @message like /CUSTOMER_METRIC/
| parse @message /CUSTOMER_METRIC: (?<metric_json>.*)/
| parse metric_json /"duration_ms":\s*(?<duration_ms>[0-9.]+)/
| parse metric_json /"operation":\s*"(?<operation>[^"]*)"/
| stats avg(duration_ms), max(duration_ms), count() by bin(5m), operation
| sort @timestamp desc
```

## Contact Information

**For Technical Issues:**
- Engineering Team: engineering@company.com
- On-call Engineer: +1-XXX-XXX-XXXX

**For Customer Escalations:**
- Customer Success Manager: success@company.com
- Support Manager: support-manager@company.com