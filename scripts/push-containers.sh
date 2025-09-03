#!/bin/bash

# Push container images to ECR (without updating Lambda functions)
# This script only builds and pushes images

set -e

# Configuration
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="088153174619"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_TAG="${1:-$(date +%Y%m%d-%H%M%S)}"

# Services configuration
SERVICES=(
    "bank-account-setup"
    "payment-processing"
    "subscription-manager"
)

echo "📤 Pushing container images to ECR..."
echo "Region: $AWS_REGION"
echo "Image Tag: $IMAGE_TAG"
echo ""

# Login to ECR
echo "📝 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Process each service
for service_dir in "${SERVICES[@]}"; do
    ecr_repository="utility-customer-$service_dir"
    image_name="utility-customer-$service_dir"
    
    echo ""
    echo "🏗️  Processing service: $service_dir"
    echo "   ECR Repository: $ecr_repository"
    
    # Build Docker image for x86_64 architecture (Lambda default) with Docker format
    echo "   📦 Building Docker image for x86_64 (Docker format)..."
    docker build --platform linux/amd64 --provenance=false --sbom=false -t $image_name:$IMAGE_TAG services/$service_dir/
    
    # Tag for ECR
    docker tag $image_name:$IMAGE_TAG $ECR_REGISTRY/$ecr_repository:$IMAGE_TAG
    docker tag $image_name:$IMAGE_TAG $ECR_REGISTRY/$ecr_repository:latest
    
    # Push to ECR
    echo "   📤 Pushing to ECR..."
    docker push $ECR_REGISTRY/$ecr_repository:$IMAGE_TAG
    docker push $ECR_REGISTRY/$ecr_repository:latest
    
    echo "   ✅ $service_dir pushed successfully!"
done

echo ""
echo "🎉 All container images pushed to ECR!"
echo ""
echo "📋 Images pushed:"
for service_dir in "${SERVICES[@]}"; do
    ecr_repository="utility-customer-$service_dir"
    echo "   - $ECR_REGISTRY/$ecr_repository:$IMAGE_TAG"
    echo "   - $ECR_REGISTRY/$ecr_repository:latest"
done