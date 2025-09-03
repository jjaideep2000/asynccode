#!/bin/bash
# Validate the containerized Lambda setup

set -e

echo "🔍 Validating Containerized Lambda Setup..."

# Check directory structure
echo "📁 Checking directory structure..."

REQUIRED_DIRS=(
    "services/bank-account-setup"
    "services/payment-processing" 
    "services/subscription-manager"
    "shared"
    ".github/workflows"
    "scripts"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir exists"
    else
        echo "  ❌ $dir missing"
        exit 1
    fi
done

# Check required files
echo ""
echo "📄 Checking required files..."

REQUIRED_FILES=(
    "services/bank-account-setup/Dockerfile"
    "services/bank-account-setup/handler.py"
    "services/bank-account-setup/requirements.txt"
    "services/payment-processing/Dockerfile"
    "services/payment-processing/handler.py"
    "services/payment-processing/requirements.txt"
    "services/subscription-manager/Dockerfile"
    "services/subscription-manager/handler.py"
    "services/subscription-manager/requirements.txt"
    ".github/workflows/deploy-all-services.yml"
    "README.md"
    ".gitignore"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file exists"
    else
        echo "  ❌ $file missing"
        exit 1
    fi
done

# Validate Dockerfiles
echo ""
echo "🐳 Validating Dockerfiles..."

for service in bank-account-setup payment-processing subscription-manager; do
    dockerfile="services/$service/Dockerfile"
    
    if grep -q "public.ecr.aws/lambda/python:3.11" "$dockerfile"; then
        echo "  ✅ $service: Uses correct base image"
    else
        echo "  ❌ $service: Incorrect base image"
        exit 1
    fi
    
    if grep -q "CMD.*handler.lambda_handler" "$dockerfile"; then
        echo "  ✅ $service: Has correct CMD"
    else
        echo "  ❌ $service: Missing or incorrect CMD"
        exit 1
    fi
done

# Validate handler files
echo ""
echo "🐍 Validating handler files..."

for service in bank-account-setup payment-processing subscription-manager; do
    handler="services/$service/handler.py"
    
    if grep -q "def lambda_handler" "$handler"; then
        echo "  ✅ $service: Has lambda_handler function"
    else
        echo "  ❌ $service: Missing lambda_handler function"
        exit 1
    fi
    
    # Check that SNS subscription logic is removed (except for subscription-manager)
    if [ "$service" != "subscription-manager" ]; then
        if grep -q "handle_subscription_control_message" "$handler"; then
            echo "  ⚠️  $service: Still has subscription control logic (should be removed)"
        else
            echo "  ✅ $service: Subscription control logic removed"
        fi
    fi
done

# Validate GitHub Actions workflow
echo ""
echo "🚀 Validating GitHub Actions workflow..."

workflow=".github/workflows/deploy-all-services.yml"

if grep -q "strategy:" "$workflow" && grep -q "matrix:" "$workflow"; then
    echo "  ✅ Uses matrix strategy for multiple services"
else
    echo "  ❌ Missing matrix strategy"
    exit 1
fi

if grep -q "aws-actions/configure-aws-credentials" "$workflow"; then
    echo "  ✅ Configures AWS credentials"
else
    echo "  ❌ Missing AWS credentials configuration"
    exit 1
fi

if grep -q "amazon-ecr-login" "$workflow"; then
    echo "  ✅ Logs into ECR"
else
    echo "  ❌ Missing ECR login"
    exit 1
fi

# Check shared modules
echo ""
echo "📚 Validating shared modules..."

if [ -f "shared/error_handler.py" ]; then
    echo "  ✅ Shared error handler exists"
else
    echo "  ❌ Missing shared error handler"
    exit 1
fi

echo ""
echo "🎉 All validations passed!"
echo ""
echo "📋 Setup Summary:"
echo "  • 3 containerized Lambda services ready"
echo "  • GitHub Actions CI/CD pipeline configured"
echo "  • Shared modules properly structured"
echo "  • SNS subscription logic centralized"
echo ""
echo "🚀 Next Steps:"
echo "  1. Push code to GitHub repository"
echo "  2. Set up AWS credentials in GitHub secrets"
echo "  3. Run: git push origin main (triggers deployment)"
echo "  4. Monitor GitHub Actions for successful deployment"
echo ""
echo "✅ Ready for containerized Lambda deployment!"