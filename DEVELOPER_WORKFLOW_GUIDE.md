# 👨‍💻 Developer Workflow Guide

## 🎯 **Simple Developer Experience**

Your team now has a **fully automated CI/CD pipeline**. Developers just need to commit code, and everything else happens automatically!

---

## 🚀 **Daily Developer Workflow**

### **1. Make Changes**
```bash
# Create a feature branch
git checkout -b feature/improve-payment-logic

# Make your code changes
# Edit services/payment-processing/handler.py
# Update tests if needed
```

### **2. Test Locally (Optional)**
```bash
# Run local tests
python -m pytest tests/

# Validate structure
./scripts/validate-setup.sh

# Test containerized build (optional)
cd services/payment-processing
docker build -t test-payment .
```

### **3. Commit & Push**
```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add enhanced payment validation logic"

# Push to GitHub
git push origin feature/improve-payment-logic
```

### **4. Create Pull Request**
- Go to GitHub and create a PR
- **Pipeline automatically runs tests** ✅
- Code review by team members
- Merge when approved

### **5. Automatic Deployment**
```bash
# When PR is merged to main:
# ✅ Pipeline builds containers
# ✅ Pushes to ECR
# ✅ Updates Lambda functions
# ✅ Runs smoke tests
# ✅ Notifies team of success/failure
```

---

## 📊 **What Happens Automatically**

### **On Pull Request:**
```
🧪 Tests run automatically
📋 Code structure validation
❌ Blocks merge if tests fail
✅ Green checkmark when ready
```

### **On Merge to Main:**
```
🏗️  Builds Docker containers (parallel)
📦 Pushes to ECR with proper tags
🚀 Updates Lambda functions
🧪 Runs smoke tests
📊 Reports deployment status
```

---

## 🔍 **Monitoring Your Changes**

### **GitHub Actions Dashboard**
- Go to your repo → Actions tab
- See real-time pipeline progress
- View logs for any failures
- Track deployment history

### **AWS Console**
- Lambda functions update automatically
- CloudWatch logs show your changes
- ECR shows new container images

---

## 🛠️ **Troubleshooting**

### **Pipeline Fails on Tests**
```bash
# Check the Actions tab for error details
# Fix the failing tests
# Commit the fix - pipeline runs again
```

### **Deployment Fails**
```bash
# Pipeline automatically shows the error
# Common issues:
#   - AWS permissions
#   - Container build errors
#   - Lambda function issues
```

### **Need to Rollback**
```bash
# Create a revert commit
git revert <commit-hash>
git push origin main
# Pipeline automatically deploys the rollback
```

---

## 📝 **Best Practices**

### **Commit Messages**
```bash
feat: add new payment validation
fix: resolve bank account bug  
docs: update API documentation
test: add unit tests for payments
ci: improve pipeline performance
```

### **Branch Naming**
```bash
feature/payment-improvements
bugfix/account-validation
hotfix/critical-security-patch
```

### **Code Changes**
- Keep changes focused and small
- Update tests when changing logic
- Test locally before pushing
- Write descriptive commit messages

---

## 🎯 **Quick Reference**

### **File Structure**
```
services/
├── bank-account-setup/
│   ├── handler.py          # ← Edit your Lambda code here
│   ├── requirements.txt    # ← Add Python dependencies
│   └── Dockerfile         # ← Usually no changes needed
├── payment-processing/
└── subscription-manager/
```

### **Common Commands**
```bash
# Start new feature
git checkout -b feature/my-feature

# Check pipeline status
gh run list

# View pipeline logs
gh run view --log

# Quick deploy test
git commit -m "test: trigger pipeline" --allow-empty
git push origin main
```

---

## 🎉 **That's It!**

**Your development workflow is now:**

1. **Write code** ✍️
2. **Commit & push** 📤  
3. **Create PR** 🔄
4. **Merge** ✅
5. **Automatic deployment** 🚀

**No manual deployments, no Jenkins setup, no infrastructure management needed!**

The pipeline handles everything automatically, giving you fast feedback and reliable deployments every time. 🏆