#!/bin/bash

# Setup ECR repositories for containerized Lambda functions
# This script creates ECR repositories if they don't exist

set -e

# Configuration
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="088153174619"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Services to create repositories for
SERVICES=(
    "utility-customer-bank-account-setup"
    "utility-customer-payment-processing"
    "utility-customer-subscription-manager"
)

echo "🚀 Setting up ECR repositories..."
echo "Region: $AWS_REGION"
echo "Account: $AWS_ACCOUNT_ID"
echo ""

# Login to ECR
echo "📝 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Create repositories
for service in "${SERVICES[@]}"; do
    echo "🏗️  Creating repository: $service"
    
    # Check if repository exists
    if aws ecr describe-repositories --repository-names $service --region $AWS_REGION --output text >/dev/null 2>&1; then
        echo "✅ Repository $service already exists"
    else
        # Create repository
        aws ecr create-repository \
            --repository-name $service \
            --region $AWS_REGION \
            --image-scanning-configuration scanOnPush=true \
            --output text >/dev/null
        
        echo "✅ Created repository: $service"
    fi
    
    # Set lifecycle policy to keep only latest 10 images
    aws ecr put-lifecycle-policy \
        --repository-name $service \
        --region $AWS_REGION \
        --output text \
        --lifecycle-policy-text '{
            "rules": [
                {
                    "rulePriority": 1,
                    "description": "Keep only 10 most recent images",
                    "selection": {
                        "tagStatus": "any",
                        "countType": "imageCountMoreThan",
                        "countNumber": 10
                    },
                    "action": {
                        "type": "expire"
                    }
                }
            ]
        }' >/dev/null
    
    echo "📋 Set lifecycle policy for $service"
done

echo ""
echo "🎉 ECR repositories setup complete!"
echo ""
echo "📋 Repository URLs:"
for service in "${SERVICES[@]}"; do
    echo "  $service: $ECR_REGISTRY/$service"
done