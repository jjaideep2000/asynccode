#!/bin/bash

# Setup GitHub Actions for Containerized Lambda Deployment
# This script helps configure the CI/CD pipeline

set -e

echo "🚀 Setting up GitHub Actions CI/CD Pipeline"
echo "==========================================="

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "📥 Install it from: https://cli.github.com/"
    echo "   Or run: brew install gh"
    exit 1
fi

# Check if user is logged in to GitHub
if ! gh auth status &> /dev/null; then
    echo "🔐 Please login to GitHub CLI first:"
    echo "   gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is ready"

# Get AWS credentials
echo ""
echo "🔧 AWS Credentials Setup"
echo "========================"

if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "📝 Enter your AWS Access Key ID for CI/CD:"
    read -r AWS_ACCESS_KEY_ID
fi

if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "📝 Enter your AWS Secret Access Key for CI/CD:"
    read -rs AWS_SECRET_ACCESS_KEY
fi

# Set GitHub secrets
echo ""
echo "🔒 Setting GitHub repository secrets..."

gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"

echo "✅ GitHub secrets configured successfully!"

# Check current repository
REPO_INFO=$(gh repo view --json name,owner)
REPO_NAME=$(echo "$REPO_INFO" | jq -r '.name')
REPO_OWNER=$(echo "$REPO_INFO" | jq -r '.owner.login')

echo ""
echo "📋 Repository Information"
echo "========================"
echo "Repository: $REPO_OWNER/$REPO_NAME"
echo "Pipeline: .github/workflows/deploy-all-services.yml"

# Check if workflow file exists
if [ -f ".github/workflows/deploy-all-services.yml" ]; then
    echo "✅ Workflow file exists"
else
    echo "❌ Workflow file not found"
    echo "   Expected: .github/workflows/deploy-all-services.yml"
    exit 1
fi

echo ""
echo "🎯 Next Steps"
echo "============="
echo "1. ✅ GitHub secrets are configured"
echo "2. ✅ Workflow file is ready"
echo "3. 🔄 Make a commit to trigger the pipeline:"
echo ""
echo "   git add ."
echo "   git commit -m \"feat: trigger CI/CD pipeline\""
echo "   git push origin main"
echo ""
echo "4. 📊 Monitor the pipeline:"
echo "   https://github.com/$REPO_OWNER/$REPO_NAME/actions"
echo ""
echo "🎉 Your DevOps pipeline is ready to go!"

# Optional: Create a test commit
echo ""
read -p "🤔 Would you like to create a test commit to trigger the pipeline? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📝 Creating test commit..."
    
    # Add a timestamp to trigger the pipeline
    echo "# Pipeline Test - $(date)" >> .pipeline-test
    git add .pipeline-test
    git commit -m "ci: test automated deployment pipeline"
    
    echo "🚀 Pushing to trigger pipeline..."
    git push origin main
    
    echo ""
    echo "🎉 Pipeline triggered! Check the Actions tab in GitHub:"
    echo "   https://github.com/$REPO_OWNER/$REPO_NAME/actions"
fi

echo ""
echo "✅ Setup complete!"