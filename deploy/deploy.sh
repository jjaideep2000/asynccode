#!/bin/bash

# Utility Customer System Deployment Script

set -e

echo "🚀 Deploying Utility Customer System"
echo "===================================="

# Configuration
PROJECT_NAME="utility-customer-system"
ENVIRONMENT="dev"
AWS_REGION="us-east-2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install AWS CLI."
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform not found. Please install Terraform."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity --output text &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure'."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create deployment packages
create_lambda_packages() {
    print_status "Creating Lambda deployment packages..."
    
    # Create deploy directory if it doesn't exist
    mkdir -p deploy
    
    # Package Bank Account Lambda
    print_status "Packaging Bank Account Lambda..."
    cd ../src/lambdas/bank-account
    
    # Create temporary directory for packaging
    mkdir -p temp_package
    
    # Copy handler and shared code
    cp handler.py temp_package/
    cp -r ../../shared temp_package/
    
    # Install dependencies
    pip3 install -r requirements.txt -t temp_package/
    
    # Create zip file
    cd temp_package
    zip -r ../../../../deploy/bank-account-setup.zip .
    cd ..
    rm -rf temp_package
    cd ../../../..
    
    print_success "Bank Account Lambda packaged"
    
    # Package Payment Lambda
    print_status "Packaging Payment Lambda..."
    cd src/lambdas/payment
    
    # Create temporary directory for packaging
    mkdir -p temp_package
    
    # Copy handler and shared code
    cp handler.py temp_package/
    cp -r ../../shared temp_package/
    
    # Install dependencies
    pip3 install -r requirements.txt -t temp_package/
    
    # Create zip file
    cd temp_package
    zip -r ../../../../deploy/payment-processing.zip .
    cd ..
    rm -rf temp_package
    cd ../../..
    
    print_success "Payment Lambda packaged"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan \
        -var="aws_region=${AWS_REGION}" \
        -var="environment=${ENVIRONMENT}" \
        -var="project_name=${PROJECT_NAME}"
    
    # Apply deployment
    terraform apply \
        -var="aws_region=${AWS_REGION}" \
        -var="environment=${ENVIRONMENT}" \
        -var="project_name=${PROJECT_NAME}" \
        -auto-approve
    
    cd ..
    
    print_success "Infrastructure deployed"
}

# Get deployment outputs
get_outputs() {
    print_status "Getting deployment outputs..."
    
    cd terraform
    
    # Get outputs
    TRANSACTION_TOPIC_ARN=$(terraform output -raw transaction_processing_topic_arn)
    SUBSCRIPTION_CONTROL_TOPIC_ARN=$(terraform output -raw subscription_control_topic_arn)
    BANK_ACCOUNT_QUEUE_URL=$(terraform output -raw bank_account_setup_queue_url)
    PAYMENT_QUEUE_URL=$(terraform output -raw payment_processing_queue_url)
    BANK_ACCOUNT_LAMBDA_NAME=$(terraform output -raw bank_account_lambda_name)
    PAYMENT_LAMBDA_NAME=$(terraform output -raw payment_lambda_name)
    
    cd ..
    
    # Save outputs to file
    cat > deploy/outputs.json << EOF
{
    "transaction_processing_topic_arn": "${TRANSACTION_TOPIC_ARN}",
    "subscription_control_topic_arn": "${SUBSCRIPTION_CONTROL_TOPIC_ARN}",
    "bank_account_setup_queue_url": "${BANK_ACCOUNT_QUEUE_URL}",
    "payment_processing_queue_url": "${PAYMENT_QUEUE_URL}",
    "bank_account_lambda_name": "${BANK_ACCOUNT_LAMBDA_NAME}",
    "payment_lambda_name": "${PAYMENT_LAMBDA_NAME}",
    "region": "${AWS_REGION}",
    "environment": "${ENVIRONMENT}"
}
EOF
    
    print_success "Outputs saved to deploy/outputs.json"
}

# Create test scripts
create_test_scripts() {
    print_status "Creating test scripts..."
    
    # Create simple test message script
    cat > tests/send_test_messages.py << 'EOF'
#!/usr/bin/env python3
"""
Send test messages to the FIFO utility customer system
"""

import json
import boto3
import random
import uuid
from datetime import datetime

def load_outputs():
    """Load deployment outputs"""
    with open('../deploy/outputs.json', 'r') as f:
        return json.load(f)

def send_transaction_message(sns_client, topic_arn, transaction_type, customer_id, **kwargs):
    """Send transaction message to FIFO SNS topic"""
    
    message_id = f"{transaction_type}-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"
    
    message = {
        "message_id": message_id,
        "transaction_type": transaction_type,
        "customer_id": customer_id,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    message_attributes = {
        'transaction_type': {
            'DataType': 'String',
            'StringValue': transaction_type
        }
    }
    
    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=json.dumps(message),
        Subject=f"Transaction: {transaction_type}",
        MessageAttributes=message_attributes,
        MessageGroupId=customer_id,
        MessageDeduplicationId=message_id
    )
    
    print(f"✅ Sent {transaction_type} message for {customer_id}")
    return response['MessageId']

def main():
    outputs = load_outputs()
    sns_client = boto3.client('sns', region_name=outputs['region'])
    
    print("🧪 Sending test messages to FIFO system...")
    
    customers = [
        "CUST-001-PREMIUM",
        "CUST-002-STANDARD", 
        "CUST-ERROR400-TEST",
        "CUST-ERROR500-TEST"
    ]
    
    topic_arn = outputs['transaction_processing_topic_arn']
    
    # Send bank account setup messages
    for customer in customers:
        send_transaction_message(
            sns_client, topic_arn, "bank_account_setup", customer,
            routing_number=f"{random.randint(100000000, 999999999)}",
            account_number=f"{random.randint(1000000000, 9999999999)}",
            account_type="checking"
        )
    
    # Send payment messages
    for customer in customers:
        amount = random.uniform(50, 500)
        send_transaction_message(
            sns_client, topic_arn, "payment", customer,
            amount=round(amount, 2),
            payment_method="bank_account",
            bill_type="utility"
        )
    
    print(f"\n🎉 Sent {len(customers) * 2} test messages!")
    print("💡 Messages will be routed to appropriate queues based on transaction_type")

if __name__ == "__main__":
    main()
EOF
    
    chmod +x tests/send_test_messages.py
    chmod +x tests/test_fifo_system.py
    
    print_success "Test scripts created"
}

# Main deployment function
main() {
    print_status "Starting deployment of ${PROJECT_NAME}..."
    
    # Run deployment steps
    check_prerequisites
    create_lambda_packages
    deploy_infrastructure
    get_outputs
    create_test_scripts
    
    print_success "🎉 Deployment completed successfully!"
    
    echo ""
    echo "📋 Next Steps:"
    echo "1. Test the system: cd tests && python3 test_fifo_system.py"
    echo "2. Monitor CloudWatch metrics in the OTEL/UtilityCustomer/Enhanced namespace"
    echo "3. Check Lambda logs for processing details"
    echo "4. Use the subscription control topic to start/stop processing"
    
    echo ""
    echo "📊 Key Resources:"
    echo "- Transaction Processing Topic (FIFO): ${TRANSACTION_TOPIC_ARN}"
    echo "- Subscription Control Topic: ${SUBSCRIPTION_CONTROL_TOPIC_ARN}"
    echo "- Bank Account Queue (FIFO): ${BANK_ACCOUNT_QUEUE_URL}"
    echo "- Payment Queue (FIFO): ${PAYMENT_QUEUE_URL}"
}

# Run main function
main "$@"