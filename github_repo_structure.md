# GitHub Repository Structure for Containerized Lambda Services

## 🏗️ Recommended Repository Structure

```
asynccode/
├── .github/
│   └── workflows/
│       ├── deploy-bank-account.yml
│       ├── deploy-payment-processing.yml
│       ├── deploy-subscription-manager.yml
│       └── deploy-all-services.yml
├── services/
│   ├── bank-account-setup/
│   │   ├── Dockerfile
│   │   ├── handler.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_handler.py
│   ├── payment-processing/
│   │   ├── Dockerfile
│   │   ├── handler.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_handler.py
│   └── subscription-manager/
│       ├── Dockerfile
│       ├── handler.py
│       ├── requirements.txt
│       └── tests/
│           └── test_handler.py
├── shared/
│   ├── __init__.py
│   ├── error_handler.py
│   ├── otel_config.py
│   └── utils.py
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── lambda.tf
│   │   ├── sqs.tf
│   │   ├── sns.tf
│   │   └── variables.tf
│   └── cloudformation/
│       └── template.yaml
├── scripts/
│   ├── build-all.sh
│   ├── deploy-local.sh
│   └── test-all.sh
├── tests/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── architecture.md
│   ├── deployment.md
│   └── api.md
├── .gitignore
├── README.md
└── docker-compose.yml
```

## 📦 Service-Specific Dockerfiles

### Bank Account Setup Service
```dockerfile
# services/bank-account-setup/Dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy shared modules
COPY ../../shared ${LAMBDA_TASK_ROOT}/shared

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["handler.lambda_handler"]
```

### Payment Processing Service
```dockerfile
# services/payment-processing/Dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy shared modules
COPY ../../shared ${LAMBDA_TASK_ROOT}/shared

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["handler.lambda_handler"]
```

### Subscription Manager Service
```dockerfile
# services/subscription-manager/Dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy function code
COPY handler.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["handler.lambda_handler"]
```

## 🚀 GitHub Actions CI/CD Pipeline

### Main Deployment Workflow
```yaml
# .github/workflows/deploy-all-services.yml
name: Deploy All Lambda Services

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-2
  ECR_REGISTRY: 088153174619.dkr.ecr.us-east-2.amazonaws.com

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest boto3 moto
      
      - name: Run tests
        run: |
          pytest tests/ -v

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    strategy:
      matrix:
        service: [bank-account-setup, payment-processing, subscription-manager]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REPOSITORY: utility-customer-${{ matrix.service }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          # Create ECR repository if it doesn't exist
          aws ecr describe-repositories --repository-names $ECR_REPOSITORY || \
          aws ecr create-repository --repository-name $ECR_REPOSITORY
          
          # Build and push Docker image
          cd services/${{ matrix.service }}
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update Lambda function
        env:
          ECR_REPOSITORY: utility-customer-${{ matrix.service }}
          IMAGE_TAG: ${{ github.sha }}
          FUNCTION_NAME: utility-customer-system-dev-${{ matrix.service }}
        run: |
          aws lambda update-function-code \
            --function-name $FUNCTION_NAME \
            --image-uri $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```

### Service-Specific Workflows
```yaml
# .github/workflows/deploy-bank-account.yml
name: Deploy Bank Account Service

on:
  push:
    paths:
      - 'services/bank-account-setup/**'
      - 'shared/**'
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-2
      
      - name: Deploy Bank Account Service
        run: |
          cd services/bank-account-setup
          ./deploy.sh
```

## 🛠️ Build and Deployment Scripts

### Universal Build Script
```bash
#!/bin/bash
# scripts/build-all.sh

set -e

SERVICES=("bank-account-setup" "payment-processing" "subscription-manager")
AWS_ACCOUNT_ID="088153174619"
AWS_REGION="us-east-2"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Building all Lambda services..."

for service in "${SERVICES[@]}"; do
    echo "Building $service..."
    
    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names "utility-customer-$service" || \
    aws ecr create-repository --repository-name "utility-customer-$service"
    
    # Build and push Docker image
    cd "services/$service"
    
    docker build -t "$ECR_REGISTRY/utility-customer-$service:latest" .
    docker push "$ECR_REGISTRY/utility-customer-$service:latest"
    
    echo "✅ Built and pushed $service"
    cd ../..
done

echo "🎉 All services built successfully!"
```

### Individual Service Deploy Script
```bash
#!/bin/bash
# services/bank-account-setup/deploy.sh

set -e

SERVICE_NAME="bank-account-setup"
FUNCTION_NAME="utility-customer-system-dev-$SERVICE_NAME"
AWS_ACCOUNT_ID="088153174619"
AWS_REGION="us-east-2"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_REPOSITORY="utility-customer-$SERVICE_NAME"

echo "Deploying $SERVICE_NAME..."

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push image
docker build -t "$ECR_REGISTRY/$ECR_REPOSITORY:latest" .
docker push "$ECR_REGISTRY/$ECR_REPOSITORY:latest"

# Update Lambda function
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --image-uri "$ECR_REGISTRY/$ECR_REPOSITORY:latest"

echo "✅ $SERVICE_NAME deployed successfully!"
```

## 🧪 Testing Structure

### Unit Tests
```python
# services/bank-account-setup/tests/test_handler.py
import pytest
import json
from unittest.mock import patch, MagicMock
from handler import lambda_handler, process_bank_account_message

def test_lambda_handler_success():
    """Test successful bank account processing"""
    event = {
        'Records': [{
            'eventSource': 'aws:sqs',
            'body': json.dumps({
                'customer_id': 'test-customer-123',
                'routing_number': '123456789',
                'account_number': '987654321'
            })
        }]
    }
    
    context = MagicMock()
    
    result = lambda_handler(event, context)
    
    assert result['statusCode'] == 200
    response_body = json.loads(result['body'])
    assert response_body['successful'] == 1

def test_process_bank_account_message_error():
    """Test error handling in bank account processing"""
    message_body = {
        'customer_id': 'ERROR500-test-customer',
        'routing_number': '123456789',
        'account_number': '987654321'
    }
    
    result = process_bank_account_message(message_body)
    
    assert result['status'] == 'error'
    assert 'unavailable' in result['error']
```

### Integration Tests
```python
# tests/integration/test_end_to_end.py
import boto3
import json
import pytest
from moto import mock_lambda, mock_sqs, mock_sns

@mock_lambda
@mock_sqs
@mock_sns
def test_end_to_end_flow():
    """Test complete message flow from SNS to Lambda"""
    # Setup mocked AWS services
    # Test message flow
    # Verify results
    pass
```

## 📋 Migration Steps

### Step 1: Repository Setup
```bash
# Clone and setup repository
git clone https://github.com/jjaideep2000/asynccode.git
cd asynccode

# Create directory structure
mkdir -p services/{bank-account-setup,payment-processing,subscription-manager}
mkdir -p shared infrastructure/{terraform,cloudformation} scripts tests/{integration,e2e} docs
```

### Step 2: Move Existing Code
```bash
# Copy Lambda functions to services
cp src/lambdas/bank-account/handler.py services/bank-account-setup/
cp src/lambdas/payment/handler.py services/payment-processing/
cp src/lambdas/subscription-manager/handler.py services/subscription-manager/

# Copy shared modules
cp -r src/shared/* shared/
```

### Step 3: Create Dockerfiles
```bash
# Create Dockerfiles for each service
# (Use the Dockerfile templates above)
```

### Step 4: Setup CI/CD
```bash
# Create GitHub Actions workflows
# (Use the workflow templates above)
```

### Step 5: Deploy Infrastructure
```bash
# Deploy using Terraform or CloudFormation
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## 🔧 Local Development

### Docker Compose for Local Testing
```yaml
# docker-compose.yml
version: '3.8'
services:
  bank-account-setup:
    build: ./services/bank-account-setup
    environment:
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - AWS_DEFAULT_REGION=us-east-2
    ports:
      - "9000:8080"
  
  payment-processing:
    build: ./services/payment-processing
    environment:
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - AWS_DEFAULT_REGION=us-east-2
    ports:
      - "9001:8080"
  
  subscription-manager:
    build: ./services/subscription-manager
    environment:
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - AWS_DEFAULT_REGION=us-east-2
    ports:
      - "9002:8080"
  
  localstack:
    image: localstack/localstack
    ports:
      - "4566:4566"
    environment:
      - SERVICES=lambda,sqs,sns
      - DEBUG=1
```

## 🎯 Benefits of This Structure

✅ **Microservices Architecture** - Each Lambda is independently deployable  
✅ **Containerized Deployment** - Consistent runtime environments  
✅ **CI/CD Pipeline** - Automated testing and deployment  
✅ **Scalable Structure** - Easy to add new services  
✅ **Shared Code Management** - Common utilities in shared module  
✅ **Infrastructure as Code** - Terraform/CloudFormation templates  
✅ **Local Development** - Docker Compose for testing  
✅ **Comprehensive Testing** - Unit, integration, and E2E tests  

This structure provides a production-ready, scalable foundation for your Lambda microservices!