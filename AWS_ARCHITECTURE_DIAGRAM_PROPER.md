# AWS Architecture Diagram - Utility Customer System

## Professional AWS Architecture Diagram

```mermaid
graph TB
    %% Define AWS Regions and Availability Zones
    subgraph "AWS Cloud - us-east-2"
        subgraph "VPC (Optional)"
            
            %% Client/External Layer
            subgraph "External/Client Layer"
                Client[fa:fa-desktop Client Applications<br/>Demo Scripts]
                ExtBank[fa:fa-university Bank Validation Service<br/>External API]
                ExtPayment[fa:fa-credit-card Payment Gateway<br/>External API]
            end
            
            %% Application Layer
            subgraph "Application Layer"
                subgraph "AWS Lambda"
                    LambdaBank[fa:fa-code Bank Account Lambda<br/>utility-customer-system-dev-bank-account-setup<br/>Runtime: Python 3.9]
                    LambdaPayment[fa:fa-code Payment Processing Lambda<br/>utility-customer-system-dev-payment-processing<br/>Runtime: Python 3.9]
                end
            end
            
            %% Messaging Layer
            subgraph "Messaging & Queuing Layer"
                subgraph "Amazon SNS"
                    SNSMain[fa:fa-bullhorn Transaction Processing Topic<br/>utility-customer-system-dev-transaction-processing.fifo<br/>Type: FIFO Topic]
                    SNSControl[fa:fa-bullhorn Subscription Control Topic<br/>utility-customer-system-dev-subscription-control<br/>Type: Standard Topic]
                end
                
                subgraph "Amazon SQS"
                    SQSBank[fa:fa-inbox Bank Account Queue<br/>utility-customer-system-dev-bank-account-setup.fifo<br/>Type: FIFO Queue]
                    SQSPayment[fa:fa-inbox Payment Processing Queue<br/>utility-customer-system-dev-payment-processing.fifo<br/>Type: FIFO Queue]
                end
            end
            
            %% Monitoring Layer
            subgraph "Monitoring & Logging"
                subgraph "Amazon CloudWatch"
                    CWLogs[fa:fa-file-text CloudWatch Logs<br/>/aws/lambda/utility-customer-system-dev-*]
                    CWMetrics[fa:fa-line-chart CloudWatch Metrics<br/>Lambda & SQS Performance]
                end
            end
            
            %% Security Layer
            subgraph "Security & Access Control"
                subgraph "AWS IAM"
                    IAMRole[fa:fa-shield Lambda Execution Roles<br/>SNS, SQS, Lambda Permissions]
                end
            end
        end
    end
    
    %% Message Flow Connections
    Client -->|Publish Messages<br/>MessageAttributes:<br/>transaction_type| SNSMain
    
    %% SNS to SQS with Filters
    SNSMain -->|Filter Policy:<br/>transaction_type = ["bank_account_setup"]| SQSBank
    SNSMain -->|Filter Policy:<br/>transaction_type = ["payment"]| SQSPayment
    
    %% SQS to Lambda Event Source Mappings
    SQSBank -->|Event Source Mapping<br/>UUID: f09739bf-eb79-4047-a97c-b6de64b8b893| LambdaBank
    SQSPayment -->|Event Source Mapping<br/>UUID: 045e3618-a858-44dc-9fde-4e8ca985795e| LambdaPayment
    
    %% Lambda to External Services
    LambdaBank -->|HTTPS API Calls<br/>Bank Account Validation| ExtBank
    LambdaPayment -->|HTTPS API Calls<br/>Payment Processing| ExtPayment
    
    %% Control Flow
    Client -->|Recovery Signals<br/>action: enable/disable| SNSControl
    SNSControl -->|Subscription Control Messages| LambdaBank
    SNSControl -->|Subscription Control Messages| LambdaPayment
    
    %% Monitoring Connections
    LambdaBank -.->|Logs & Metrics| CWLogs
    LambdaPayment -.->|Logs & Metrics| CWLogs
    SQSBank -.->|Queue Metrics| CWMetrics
    SQSPayment -.->|Queue Metrics| CWMetrics
    LambdaBank -.->|Function Metrics| CWMetrics
    LambdaPayment -.->|Function Metrics| CWMetrics
    
    %% Security Connections
    LambdaBank -.->|Assumes Role| IAMRole
    LambdaPayment -.->|Assumes Role| IAMRole
    
    %% Dynamic UUID Discovery (Self-referential)
    LambdaBank -.->|list_event_source_mappings()<br/>Dynamic UUID Discovery| LambdaBank
    LambdaPayment -.->|list_event_source_mappings()<br/>Dynamic UUID Discovery| LambdaPayment
    
    %% Styling for AWS Services
    classDef awsLambda fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef awsSNS fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef awsSQS fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef awsCloudWatch fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef awsIAM fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#FFFFFF
    classDef external fill:#E8F4FD,stroke:#1976D2,stroke-width:2px,color:#1976D2
    classDef client fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#7B1FA2
    
    %% Apply styles
    class LambdaBank,LambdaPayment awsLambda
    class SNSMain,SNSControl awsSNS
    class SQSBank,SQSPayment awsSQS
    class CWLogs,CWMetrics awsCloudWatch
    class IAMRole awsIAM
    class ExtBank,ExtPayment external
    class Client client
```

## AWS Service Details

### 🔧 **Compute Services**
| Service | Resource | Configuration |
|---------|----------|---------------|
| **AWS Lambda** | Bank Account Setup | Python 3.9, 512MB Memory, 5min Timeout |
| **AWS Lambda** | Payment Processing | Python 3.9, 512MB Memory, 5min Timeout |

### 📡 **Messaging Services**
| Service | Resource | Type | Configuration |
|---------|----------|------|---------------|
| **Amazon SNS** | Transaction Processing | FIFO Topic | Content-based deduplication |
| **Amazon SNS** | Subscription Control | Standard Topic | System control messages |
| **Amazon SQS** | Bank Account Queue | FIFO Queue | 14-day retention, Long polling |
| **Amazon SQS** | Payment Queue | FIFO Queue | 14-day retention, Long polling |

### 📊 **Monitoring Services**
| Service | Resource | Purpose |
|---------|----------|---------|
| **CloudWatch Logs** | Lambda Log Groups | Function execution logs |
| **CloudWatch Metrics** | Custom Metrics | Performance monitoring |

### 🔐 **Security Services**
| Service | Resource | Purpose |
|---------|----------|---------|
| **AWS IAM** | Lambda Execution Roles | Service permissions |
| **SQS Policies** | Queue Access Control | SNS-only message delivery |
| **SNS Policies** | Topic Access Control | Account-scoped publishing |

## 🎯 **Architecture Patterns Implemented**

### **1. Event-Driven Architecture**
- **Asynchronous Processing**: SNS → SQS → Lambda
- **Loose Coupling**: Services communicate via messages
- **Scalability**: Auto-scaling based on queue depth

### **2. Content-Based Routing**
- **Message Filtering**: SNS filter policies route messages
- **Attribute-Based**: `transaction_type` determines destination
- **Zero Duplication**: Each message goes to correct queue only

### **3. Circuit Breaker Pattern**
- **Error Detection**: 500 errors trigger protection
- **Subscription Control**: Dynamic enable/disable of processing
- **Graceful Degradation**: System protects itself from cascade failures

### **4. Dynamic Configuration**
- **UUID Discovery**: Runtime discovery of event source mappings
- **Environment Agnostic**: No hardcoded configuration
- **Self-Healing**: Automatic adaptation to infrastructure changes

## 🏗️ **Infrastructure as Code**

### **Terraform Resources**
```hcl
# Core messaging infrastructure
aws_sns_topic.transaction_processing          # Main FIFO topic
aws_sns_topic_subscription.bank_account_*     # Filtered subscriptions
aws_sns_topic_subscription.payment_*          # Filtered subscriptions
aws_sqs_queue.bank_account_setup             # FIFO queue
aws_sqs_queue.payment_processing             # FIFO queue

# Compute infrastructure  
aws_lambda_function.bank_account_setup       # Processing function
aws_lambda_function.payment_processing       # Processing function
aws_lambda_event_source_mapping.*            # SQS triggers

# Security infrastructure
aws_iam_role.lambda_execution_role           # Execution permissions
aws_sqs_queue_policy.*                       # Queue access control
aws_sns_topic_policy.*                       # Topic access control
```

## 📋 **Message Flow Architecture**

### **Normal Operation**
```
Client → SNS Topic → [Filter Policy] → SQS Queue → Lambda → External API
```

### **Error Handling (500 Errors)**
```
External API (500) → Lambda → Dynamic UUID Discovery → Disable Event Source Mapping
```

### **Recovery Process**
```
Operator → SNS Control Topic → Lambda Functions → Enable Event Source Mapping
```

## 🎨 **To Generate Visual Diagram**

1. **Copy the Mermaid code above** (lines 5-95)
2. **Use AWS Architecture Tools**:
   - **AWS Architecture Icons**: https://aws.amazon.com/architecture/icons/
   - **Lucidchart**: AWS architecture templates
   - **Draw.io**: AWS shape library
   - **Cloudcraft**: 3D AWS diagrams

3. **Online Mermaid Renderers**:
   - **Mermaid Live**: https://mermaid.live/
   - **Mermaid Ink**: https://mermaid.ink/

This diagram follows AWS Well-Architected Framework principles and uses standard AWS architectural patterns for enterprise-grade serverless applications.