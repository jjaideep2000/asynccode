# AWS Architecture Diagram - Utility Customer System

## System Overview
This diagram shows the complete AWS architecture for the resilient utility customer system with dynamic UUID discovery and intelligent subscription management.

```mermaid
graph TB
    %% Client Layer
    Client[🖥️ Client Applications<br/>Demo Scripts]
    
    %% SNS Layer
    subgraph "SNS - Message Routing"
        SNS_Main[📡 Transaction Processing Topic<br/>utility-customer-system-dev-transaction-processing.fifo<br/>FIFO Topic]
        SNS_Control[📢 Subscription Control Topic<br/>utility-customer-system-dev-subscription-control<br/>Standard Topic]
    end
    
    %% SQS Layer
    subgraph "SQS - Message Queues"
        SQS_Bank[📦 Bank Account Setup Queue<br/>utility-customer-system-dev-bank-account-setup.fifo<br/>FIFO Queue]
        SQS_Payment[💳 Payment Processing Queue<br/>utility-customer-system-dev-payment-processing.fifo<br/>FIFO Queue]
    end
    
    %% Lambda Layer
    subgraph "Lambda - Processing Functions"
        Lambda_Bank[🏦 Bank Account Lambda<br/>utility-customer-system-dev-bank-account-setup<br/>Dynamic UUID Discovery]
        Lambda_Payment[💰 Payment Processing Lambda<br/>utility-customer-system-dev-payment-processing<br/>Dynamic UUID Discovery]
    end
    
    %% External Services
    subgraph "External Services"
        Bank_Service[🏛️ Bank Validation Service<br/>External API]
        Payment_Gateway[💳 Payment Gateway<br/>External API]
    end
    
    %% CloudWatch
    subgraph "Monitoring & Logging"
        CW_Logs[📋 CloudWatch Logs<br/>/aws/lambda/utility-customer-system-dev-*]
        CW_Metrics[📊 CloudWatch Metrics<br/>Lambda & SQS Metrics]
    end
    
    %% IAM
    subgraph "Security & Permissions"
        IAM_Role[🔐 Lambda Execution Roles<br/>SNS, SQS, Lambda Permissions]
    end
    
    %% Message Flow - Normal Operation
    Client -->|1. Publish Message<br/>transaction_type: bank_account_setup| SNS_Main
    Client -->|1. Publish Message<br/>transaction_type: payment| SNS_Main
    
    %% SNS Subscriptions with Filters
    SNS_Main -->|Filter: transaction_type = bank_account_setup| SQS_Bank
    SNS_Main -->|Filter: transaction_type = payment| SQS_Payment
    
    %% SQS to Lambda Event Source Mappings
    SQS_Bank -->|Event Source Mapping<br/>UUID: f09739bf-eb79-4047-a97c-b6de64b8b893| Lambda_Bank
    SQS_Payment -->|Event Source Mapping<br/>UUID: 045e3618-a858-44dc-9fde-4e8ca985795e| Lambda_Payment
    
    %% Lambda to External Services
    Lambda_Bank -->|API Calls| Bank_Service
    Lambda_Payment -->|API Calls| Payment_Gateway
    
    %% Control Flow - Subscription Management
    Client -->|Recovery Signal<br/>action: enable/disable| SNS_Control
    SNS_Control -->|Control Messages| Lambda_Bank
    SNS_Control -->|Control Messages| Lambda_Payment
    
    %% Dynamic UUID Discovery
    Lambda_Bank -.->|Dynamic UUID Discovery<br/>list_event_source_mappings()| Lambda_Bank
    Lambda_Payment -.->|Dynamic UUID Discovery<br/>list_event_source_mappings()| Lambda_Payment
    
    %% Monitoring
    Lambda_Bank --> CW_Logs
    Lambda_Payment --> CW_Logs
    SQS_Bank --> CW_Metrics
    SQS_Payment --> CW_Metrics
    Lambda_Bank --> CW_Metrics
    Lambda_Payment --> CW_Metrics
    
    %% Security
    Lambda_Bank -.-> IAM_Role
    Lambda_Payment -.-> IAM_Role
    
    %% Styling
    classDef client fill:#e1f5fe
    classDef sns fill:#fff3e0
    classDef sqs fill:#f3e5f5
    classDef lambda fill:#e8f5e8
    classDef external fill:#ffebee
    classDef monitoring fill:#f1f8e9
    classDef security fill:#fce4ec
    
    class Client client
    class SNS_Main,SNS_Control sns
    class SQS_Bank,SQS_Payment sqs
    class Lambda_Bank,Lambda_Payment lambda
    class Bank_Service,Payment_Gateway external
    class CW_Logs,CW_Metrics monitoring
    class IAM_Role security
```

## Architecture Components

### 1. **Client Layer**
- **Demo Scripts**: Python scripts that simulate customer requests
- **Message Publishing**: Sends messages to SNS with proper attributes

### 2. **SNS (Simple Notification Service)**
- **Transaction Processing Topic**: FIFO topic for message routing
  - Routes messages based on `transaction_type` attribute
  - Ensures message ordering and deduplication
- **Subscription Control Topic**: Standard topic for system control
  - Sends enable/disable commands to Lambda functions

### 3. **SQS (Simple Queue Service)**
- **Bank Account Setup Queue**: FIFO queue for bank account requests
- **Payment Processing Queue**: FIFO queue for payment requests
- **Message Filtering**: Receives messages based on SNS subscription filters

### 4. **Lambda Functions**
- **Bank Account Lambda**: Processes bank account setup requests
- **Payment Processing Lambda**: Processes payment requests
- **Dynamic UUID Discovery**: Automatically discovers event source mapping UUIDs
- **Intelligent Error Handling**: Disables subscriptions on 500 errors

### 5. **External Services**
- **Bank Validation Service**: External API for bank account validation
- **Payment Gateway**: External API for payment processing

### 6. **Monitoring & Logging**
- **CloudWatch Logs**: Captures Lambda function logs
- **CloudWatch Metrics**: Monitors Lambda and SQS performance

### 7. **Security**
- **IAM Roles**: Provides necessary permissions for Lambda functions

## Message Flow Scenarios

### Normal Operation Flow
```
Client → SNS Topic → SQS Queue → Lambda Function → External Service
```

### Crisis Response Flow (500 Errors)
```
External Service (500 Error) → Lambda Function → Dynamic UUID Discovery → Disable Subscription
```

### Recovery Flow
```
Client → SNS Control Topic → Lambda Functions → Enable Subscription → Process Backlog
```

## Key Features

### 🧠 **Intelligent Error Handling**
- **400 Errors**: Continue processing (client errors)
- **500 Errors**: Disable subscriptions (server errors)
- **Automatic Protection**: Prevents cascade failures

### 🔄 **Dynamic UUID Discovery**
- **No Hardcoding**: Automatically discovers event source mapping UUIDs
- **Runtime Adaptation**: Works in any environment without configuration
- **Self-Healing**: Enables automatic subscription management

### 📡 **SNS-Based Control Plane**
- **Centralized Control**: Single point for system-wide commands
- **Scalable**: Can control multiple Lambda functions simultaneously
- **Reliable**: Uses AWS managed service for message delivery

### 🛡️ **Resilience Features**
- **Message Durability**: FIFO queues preserve message ordering
- **Zero Data Loss**: Messages safely queued during outages
- **Automatic Recovery**: System resumes processing after recovery signal
- **Cascade Prevention**: Intelligent subscription management

### 📊 **Observability**
- **Comprehensive Logging**: All operations logged to CloudWatch
- **Real-time Monitoring**: Queue depths and processing metrics
- **Traceability**: Complete audit trail of all operations

## Resource Naming Convention
```
utility-customer-system-{environment}-{component}
```

## AWS Services Used
- **SNS**: Message routing and system control
- **SQS**: Message queuing and buffering
- **Lambda**: Serverless compute for processing
- **CloudWatch**: Monitoring and logging
- **IAM**: Security and permissions

This architecture provides a highly resilient, scalable, and intelligent system for processing utility customer transactions with automatic failure detection and recovery capabilities.