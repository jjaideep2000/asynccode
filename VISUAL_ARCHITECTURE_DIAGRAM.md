# Visual AWS Architecture Diagram - Utility Customer System

## Simplified Visual Representation

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           🖥️  CLIENT APPLICATIONS                                │
│                              (Demo Scripts)                                     │
└─────────────────────┬───────────────────────────────────────────────────────────┘
                      │
                      │ 1. Publish Messages
                      │ (transaction_type: bank_account_setup | payment)
                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     📡 SNS TRANSACTION PROCESSING TOPIC                         │
│              utility-customer-system-dev-transaction-processing.fifo            │
│                              (FIFO Topic)                                       │
└─────────────────┬─────────────────────────────────┬─────────────────────────────┘
                  │                                 │
                  │ Filter:                         │ Filter:
                  │ transaction_type =              │ transaction_type = 
                  │ ["bank_account_setup"]          │ ["payment"]
                  ▼                                 ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────┐
│     📦 SQS BANK ACCOUNT QUEUE   │    │    💳 SQS PAYMENT QUEUE         │
│  bank-account-setup.fifo        │    │  payment-processing.fifo        │
│        (FIFO Queue)             │    │        (FIFO Queue)             │
└─────────────┬───────────────────┘    └─────────────┬───────────────────┘
              │                                      │
              │ Event Source Mapping                 │ Event Source Mapping
              │ UUID: f09739bf-eb79-4047...          │ UUID: 045e3618-a858-44dc...
              ▼                                      ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────┐
│    🏦 BANK ACCOUNT LAMBDA       │    │    💰 PAYMENT LAMBDA            │
│  bank-account-setup             │    │  payment-processing             │
│  Dynamic UUID Discovery         │    │  Dynamic UUID Discovery         │
└─────────────┬───────────────────┘    └─────────────┬───────────────────┘
              │                                      │
              │ API Calls                            │ API Calls
              ▼                                      ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────┐
│   🏛️  BANK VALIDATION SERVICE   │    │    💳 PAYMENT GATEWAY           │
│      (External API)             │    │      (External API)             │
└─────────────────────────────────┘    └─────────────────────────────────┘

                              ┌─────────────────────────────────┐
                              │  📢 SNS SUBSCRIPTION CONTROL    │
                              │     subscription-control        │
                              │      (Standard Topic)           │
                              └─────────────┬───────────────────┘
                                            │
                                            │ Control Messages
                                            │ (enable/disable)
                              ┌─────────────▼───────────────────┐
                              │     Both Lambda Functions       │
                              │   (Subscription Management)     │
                              └─────────────────────────────────┘

                    ┌─────────────────────────────────────────────────┐
                    │           📊 CLOUDWATCH MONITORING              │
                    │                                                 │
                    │  📋 Logs: /aws/lambda/utility-customer-*        │
                    │  📈 Metrics: Lambda & SQS Performance           │
                    └─────────────────────────────────────────────────┘
```

## 🔄 Message Flow Scenarios

### Normal Operation Flow
```
Client → SNS Topic → SQS Queue → Lambda Function → External Service
```

### 500 Error Crisis Flow
```
External Service (500 Error) → Lambda Function → Dynamic UUID Discovery → Disable Subscription
                                     ↓
                            Messages Pile Up in SQS Queue
```

### Recovery Flow
```
Client → SNS Control Topic → Lambda Functions → Enable Subscription → Process Backlog
```

## 🎯 Key Architecture Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Client Layer** | Message Publishing | Python Demo Scripts |
| **SNS Topic** | Message Routing | FIFO Topic with Filters |
| **SQS Queues** | Message Buffering | FIFO Queues |
| **Lambda Functions** | Message Processing | Serverless Compute |
| **External Services** | Business Logic | Bank API, Payment Gateway |
| **Control Plane** | System Management | SNS Standard Topic |
| **Monitoring** | Observability | CloudWatch Logs & Metrics |

## 🛡️ Resilience Features

### Content-Based Routing
- **SNS Filters**: `transaction_type = ["bank_account_setup"]` vs `["payment"]`
- **Automatic Routing**: Messages go to correct queues based on attributes
- **Zero Configuration**: No hardcoded routing logic

### Dynamic UUID Discovery
- **Runtime Discovery**: Lambda functions find their own event source mapping UUIDs
- **Environment Agnostic**: Works in dev, staging, prod without changes
- **Self-Healing**: Enables automatic subscription management

### Intelligent Error Handling
- **400 Errors**: Continue processing (client errors)
- **500 Errors**: Disable subscriptions (server errors)
- **Cascade Prevention**: Stops processing when external services fail

### Recovery Mechanisms
- **SNS Control Messages**: Centralized system recovery
- **Automatic Re-enabling**: Lambda functions respond to recovery signals
- **Backlog Processing**: Queued messages processed after recovery

## 📊 Resource Naming Convention
```
utility-customer-system-{environment}-{component}
```

## 🔐 Security Model
- **IAM Roles**: Lambda execution permissions
- **SQS Policies**: Only SNS can send messages
- **SNS Policies**: Account-scoped access control
- **VPC**: (Optional) Network isolation