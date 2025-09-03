#!/bin/bash

# Deploy containerized Lambda functions
# This script builds, pushes, and updates Lambda functions with container images

set -e

# Configuration
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="088153174619"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_TAG="${1:-$(date +%Y%m%d-%H%M%S)}"

# Services configuration
SERVICES=(
    "bank-account-setup:utility-customer-system-dev-bank-account-setup"
    "payment-processing:utility-customer-system-dev-payment-processing"
    "subscription-manager:utility-customer-system-dev-subscription-manager"
)

echo "🚀 Deploying containerized Lambda functions..."
echo "Region: $AWS_REGION"
echo "Image Tag: $IMAGE_TAG"
echo ""

# Login to ECR
echo "📝 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Process each service
for service_config in "${SERVICES[@]}"; do
    service_dir="${service_config%%:*}"
    lambda_function_name="${service_config##*:}"
    ecr_repository="utility-customer-$service_dir"
    image_name="utility-customer-$service_dir"
    
    echo ""
    echo "🏗️  Processing service: $service_dir"
    echo "   Lambda Function: $lambda_function_name"
    echo "   ECR Repository: $ecr_repository"
    
    # Build Docker image
    echo "   📦 Building Docker image..."
    docker build -t $image_name:$IMAGE_TAG services/$service_dir/
    
    # Tag for ECR
    docker tag $image_name:$IMAGE_TAG $ECR_REGISTRY/$ecr_repository:$IMAGE_TAG
    docker tag $image_name:$IMAGE_TAG $ECR_REGISTRY/$ecr_repository:latest
    
    # Push to ECR
    echo "   📤 Pushing to ECR..."
    docker push $ECR_REGISTRY/$ecr_repository:$IMAGE_TAG
    docker push $ECR_REGISTRY/$ecr_repository:latest
    
    # Update Lambda function
    echo "   🔄 Updating Lambda function..."
    aws lambda update-function-code \
        --function-name $lambda_function_name \
        --image-uri $ECR_REGISTRY/$ecr_repository:$IMAGE_TAG \
        --region $AWS_REGION
    
    # Wait for update to complete
    echo "   ⏳ Waiting for update to complete..."
    aws lambda wait function-updated \
        --function-name $lambda_function_name \
        --region $AWS_REGION
    
    echo "   ✅ $service_dir deployment complete!"
done

echo ""
echo "🎉 All containerized Lambda functions deployed successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "   Image Tag: $IMAGE_TAG"
echo "   Deployed Services:"
for service_config in "${SERVICES[@]}"; do
    service_dir="${service_config%%:*}"
    lambda_function_name="${service_config##*:}"
    ecr_repository="utility-customer-$service_dir"
    echo "     - $service_dir → $lambda_function_name"
    echo "       Image: $ECR_REGISTRY/$ecr_repository:$IMAGE_TAG"
done

echo ""
echo "🔍 To verify deployment:"
echo "   aws lambda list-functions --region $AWS_REGION --query 'Functions[?contains(FunctionName, \`utility-customer-system-dev\`)].{Name:FunctionName,Runtime:Runtime,CodeSize:CodeSize}' --output table"