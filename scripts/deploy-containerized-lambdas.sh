#!/bin/bash
# Deploy containerized Lambda functions

set -e

SERVICES=("bank-account-setup" "payment-processing" "subscription-manager")
AWS_ACCOUNT_ID="088153174619"
AWS_REGION="us-east-2"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "🚀 Deploying containerized Lambda functions..."

for service in "${SERVICES[@]}"; do
    echo "📦 Deploying $service..."
    
    FUNCTION_NAME="utility-customer-system-dev-$service"
    ECR_REPOSITORY="utility-customer-$service"
    IMAGE_URI="$ECR_REGISTRY/$ECR_REPOSITORY:latest"
    
    echo "Updating Lambda function: $FUNCTION_NAME"
    echo "Using image: $IMAGE_URI"
    
    # Update Lambda function to use container image
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --image-uri $IMAGE_URI
    
    # Wait for update to complete
    echo "Waiting for function update to complete..."
    aws lambda wait function-updated --function-name $FUNCTION_NAME
    
    echo "✅ Deployed $service successfully"
done

echo "🎉 All containerized Lambda functions deployed!"
echo ""
echo "Verifying deployments..."

for service in "${SERVICES[@]}"; do
    FUNCTION_NAME="utility-customer-system-dev-$service"
    
    echo "Checking $FUNCTION_NAME..."
    aws lambda get-function --function-name $FUNCTION_NAME --query 'Code.ImageUri' --output text
done

echo ""
echo "✅ All functions are now running as containers!"