#!/bin/bash

# Create new container-based Lambda functions
# This script creates Lambda functions using container images from ECR

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

echo "🚀 Creating container-based Lambda functions..."
echo "Region: $AWS_REGION"
echo ""

# Check if IAM role exists, create if needed
ROLE_NAME="utility-customer-lambda-execution-role"
ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$ROLE_NAME"

echo "📋 Checking IAM role..."
if aws iam get-role --role-name $ROLE_NAME --output text >/dev/null 2>&1; then
    echo "✅ IAM role $ROLE_NAME exists"
else
    echo "🏗️  Creating IAM role $ROLE_NAME..."
    
    # Create trust policy
    cat > /tmp/trust-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

    # Create role
    aws iam create-role \
        --role-name $ROLE_NAME \
        --assume-role-policy-document file:///tmp/trust-policy.json \
        --output text >/dev/null
    
    # Attach basic execution policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --output text >/dev/null
    
    # Attach SQS access policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonSQSFullAccess \
        --output text >/dev/null
    
    # Attach SNS access policy
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/AmazonSNSFullAccess \
        --output text >/dev/null
    
    # Wait for role to be available
    sleep 10
    
    echo "✅ Created IAM role $ROLE_NAME"
fi

# Process each service
for service_config in "${SERVICES[@]}"; do
    service_dir="${service_config%%:*}"
    lambda_function_name="${service_config##*:}"
    ecr_repository="utility-customer-$service_dir"
    
    echo ""
    echo "🏗️  Creating: $lambda_function_name"
    echo "   Service: $service_dir"
    echo "   Image: $ECR_REGISTRY/$ecr_repository:latest"
    
    # Check if function already exists and what package type it uses
    if aws lambda get-function-configuration --function-name $lambda_function_name --region $AWS_REGION --output json >/dev/null 2>&1; then
        package_type=$(aws lambda get-function-configuration --function-name $lambda_function_name --region $AWS_REGION --query 'PackageType' --output text)
        if [ "$package_type" = "Image" ]; then
            echo "   ✅ Function $lambda_function_name already exists as container, skipping..."
            continue
        else
            echo "   🔄 Function $lambda_function_name exists as Zip, converting to container..."
            # Get current configuration
            current_config=$(aws lambda get-function-configuration --function-name $lambda_function_name --region $AWS_REGION --output json)
            role_arn=$(echo $current_config | jq -r '.Role')
            timeout=$(echo $current_config | jq -r '.Timeout')
            memory_size=$(echo $current_config | jq -r '.MemorySize')
            description=$(echo $current_config | jq -r '.Description // "Containerized Lambda function"')
            
            # Delete existing function
            echo "   🗑️  Deleting existing Zip function..."
            aws lambda delete-function --function-name $lambda_function_name --region $AWS_REGION --output text >/dev/null
            sleep 5
        fi
    fi
    
    # Create container-based function
    echo "   🚀 Creating container-based function..."
    aws lambda create-function \
        --function-name $lambda_function_name \
        --role $ROLE_ARN \
        --code ImageUri=$ECR_REGISTRY/$ecr_repository:latest \
        --package-type Image \
        --timeout 300 \
        --memory-size 512 \
        --description "Containerized $service_dir Lambda function" \
        --region $AWS_REGION \
        --output text >/dev/null
    
    echo "   ✅ $lambda_function_name created successfully!"
done

echo ""
echo "🎉 All container-based Lambda functions created!"
echo ""
echo "🔍 Verify with:"
echo "   aws lambda list-functions --region $AWS_REGION --query 'Functions[?contains(FunctionName, \`utility-customer-system-dev\`)].{Name:FunctionName,PackageType:PackageType,Runtime:Runtime}' --output table"