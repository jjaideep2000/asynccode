# Utility Customer System - Containerized Lambda Services

A resilient, event-driven microservices architecture for utility customer management using AWS Lambda containers, SQS, and SNS.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Bank Account    │    │ Payment         │    │ Subscription    │
│ Setup Service   │    │ Processing      │    │ Manager         │
│ (Container)     │    │ Service         │    │ Service         │
│                 │    │ (Container)     │    │ (Container)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ SNS Topic       │
                    │ (Subscription   │
                    │ Control)        │
                    └─────────────────┘
```

## 🚀 Features

- **Containerized Lambda Functions** - All services run as Docker containers
- **Centralized Subscription Management** - Single service manages all Lambda subscriptions
- **Intelligent Error Handling** - Automatic circuit breaker for 500 errors
- **Event-Driven Architecture** - SNS/SQS messaging for loose coupling
- **CI/CD Pipeline** - GitHub Actions for automated deployment
- **Comprehensive Testing** - Unit, integration, and end-to-end tests

## 📦 Services

### 1. Bank Account Setup Service
- **Purpose**: Validates and sets up customer bank accounts
- **Triggers**: SQS messages from transaction processing topic
- **Container**: `services/bank-account-setup/`

### 2. Payment Processing Service
- **Purpose**: Processes utility bill payments
- **Triggers**: SQS messages from transaction processing topic
- **Container**: `services/payment-processing/`

### 3. Subscription Manager Service
- **Purpose**: Centrally manages Lambda function subscriptions
- **Triggers**: SNS messages for subscription control
- **Container**: `services/subscription-manager/`

## 🛠️ Local Development

### Prerequisites
- Docker
- AWS CLI configured
- Python 3.11+

### Setup
```bash
# Clone repository
git clone https://github.com/jjaideep2000/asynccode.git
cd asynccode

# Build all services locally
./scripts/build-all.sh

# Run local tests
docker-compose up
```

### Testing Individual Services
```bash
# Test bank account service
cd services/bank-account-setup
docker build -t bank-account-test .
docker run -p 9000:8080 bank-account-test

# Send test request
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"customer_id": "test-123", "routing_number": "123456789", "account_number": "987654321"}'
```

## 🚀 Deployment

### Automated Deployment (GitHub Actions)
1. Push to `main` branch
2. GitHub Actions automatically:
   - Runs tests
   - Builds Docker images
   - Pushes to ECR
   - Updates Lambda functions

### Manual Deployment
```bash
# Build and push all containers
./scripts/build-all.sh

# Deploy to Lambda
./scripts/deploy-containerized-lambdas.sh
```

### Environment Setup
Set these secrets in GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## 🧪 Testing

### Unit Tests
```bash
pytest services/*/tests/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### End-to-End Tests
```bash
pytest tests/e2e/ -v
```

## 📊 Monitoring and Observability

### CloudWatch Logs
- Each service logs to `/aws/lambda/utility-customer-system-dev-{service-name}`
- Structured JSON logging for easy parsing

### Metrics
- Custom CloudWatch metrics for business events
- Lambda performance metrics
- SQS queue depth monitoring

### Tracing
- AWS X-Ray integration for distributed tracing
- Custom correlation IDs for request tracking

## 🔧 Configuration

### Environment Variables
- `MANAGED_FUNCTIONS`: JSON configuration for subscription manager
- `AWS_REGION`: AWS region (default: us-east-2)
- `ENVIRONMENT`: Environment name (dev/staging/prod)

### Infrastructure
Infrastructure is managed via:
- **Terraform**: `infrastructure/terraform/`
- **CloudFormation**: `infrastructure/cloudformation/`

## 🚨 Error Handling and Resilience

### Circuit Breaker Pattern
- 500 errors automatically disable Lambda subscriptions
- Centralized recovery via SNS messages
- Prevents cascade failures

### Dead Letter Queues
- Failed messages sent to DLQ for investigation
- Configurable retry policies

### Graceful Degradation
- Services continue operating during partial failures
- Message queuing ensures no data loss

## 📈 Scaling

### Adding New Services
1. Create new service directory: `services/new-service/`
2. Add Dockerfile and handler
3. Update `MANAGED_FUNCTIONS` configuration
4. Add to CI/CD pipeline

### Performance Tuning
- Lambda memory and timeout configuration
- SQS batch size optimization
- Container image optimization

## 🔐 Security

### IAM Roles
- Least privilege access for each service
- Service-specific IAM roles
- Cross-service access via IAM policies

### Container Security
- Base images from AWS ECR Public Gallery
- Regular security scanning
- Minimal container footprint

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [API Documentation](docs/api.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in this repository
- Check the [troubleshooting guide](docs/troubleshooting.md)
- Review CloudWatch logs for error details