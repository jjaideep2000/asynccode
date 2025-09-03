#!/bin/bash
# Build and deploy all Lambda services

set -e

SERVICES=("bank-account-setup" "payment-processing" "subscription-manager")
AWS_ACCOUNT_ID="088153174619"
AWS_REGION="us-east-2"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "🚀 Building all Lambda services..."

# Login to ECR
echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

for service in "${SERVICES[@]}"; do
    echo "📦 Building $service..."
    
    # Create ECR repository if it doesn't exist
    echo "Checking ECR repository for $service..."
    aws ecr describe-repositories --repository-names "utility-customer-$service" || \
    aws ecr create-repository --repository-name "utility-customer-$service"
    
    # Build and push Docker image
    cd "services/$service"
    
    echo "Building Docker image for $service..."
    docker build -t "$ECR_REGISTRY/utility-customer-$service:latest" .
    
    echo "Pushing Docker image for $service..."
    docker push "$ECR_REGISTRY/utility-customer-$service:latest"
    
    echo "✅ Built and pushed $service"
    cd ../..
done

echo "🎉 All services built successfully!"
echo ""
echo "Next steps:"
echo "1. Update Lambda functions to use container images"
echo "2. Test the deployed services"
echo "3. Run end-to-end tests"