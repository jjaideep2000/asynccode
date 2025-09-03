#!/bin/bash

# Convert existing Lambda functions from Zip to Container package type
# This script recreates Lambda functions to use container images

set -e

# Configuration
AWS_REGION="us-east-2"
AWS_ACCOUNT_ID="088153174619"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Services configuration
SERVICES=(
    "bank-account-setup:utility-customer-system-dev-bank-account-setup"
    "payment-processing:utility-customer-system-dev-payment-processing"
    "subscription-manager:utility-customer-system-dev-subscription-manager"
)

echo "🔄 Converting Lambda functions to container package type..."
echo "Region: $AWS_REGION"
echo ""

# Process each service
for service_config in "${SERVICES[@]}"; do
    service_dir="${service_config%%:*}"
    lambda_function_name="${service_config##*:}"
    ecr_repository="utility-customer-$service_dir"
    
    echo "🏗️  Processing: $lambda_function_name"
    
    # Get current function configuration
    echo "   📋 Getting current configuration..."
    current_config=$(aws lambda get-function-configuration \
        --function-name $lambda_function_name \
        --region $AWS_REGION \
        --output json)
    
    # Extract current settings
    role_arn=$(echo $current_config | jq -r '.Role')
    timeout=$(echo $current_config | jq -r '.Timeout')
    memory_size=$(echo $current_config | jq -r '.MemorySize')
    description=$(echo $current_config | jq -r '.Description // "Containerized Lambda function"')
    
    echo "   📦 Current settings:"
    echo "      Role: $role_arn"
    echo "      Timeout: $timeout"
    echo "      Memory: $memory_size MB"
    
    # Delete existing function
    echo "   🗑️  Deleting existing function..."
    aws lambda delete-function \
        --function-name $lambda_function_name \
        --region $AWS_REGION \
        --output text >/dev/null
    
    # Wait a moment for deletion to complete
    sleep 5
    
    # Create new container-based function
    echo "   🚀 Creating container-based function..."
    aws lambda create-function \
        --function-name $lambda_function_name \
        --role $role_arn \
        --code ImageUri=$ECR_REGISTRY/$ecr_repository:latest \
        --package-type Image \
        --timeout $timeout \
        --memory-size $memory_size \
        --description "$description (Container)" \
        --region $AWS_REGION \
        --output text >/dev/null
    
    echo "   ✅ $lambda_function_name converted to container!"
done

echo ""
echo "🎉 All Lambda functions converted to container package type!"
echo ""
echo "🔍 Verify with:"
echo "   aws lambda list-functions --region $AWS_REGION --query 'Functions[?contains(FunctionName, \`utility-customer-system-dev\`)].{Name:FunctionName,PackageType:PackageType,Runtime:Runtime}' --output table"