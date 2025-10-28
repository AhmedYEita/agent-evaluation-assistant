# Pre-Commit Checks - Quick Reference

Quick commands to run before committing changes to ensure CI/CD passes.

## 📋 SDK Code Quality Checks

### ✅ Check All (run before commit)
```bash
cd sdk && python -m black --check agent_evaluation_sdk/ && python -m ruff check agent_evaluation_sdk/ && python -m mypy agent_evaluation_sdk/ && echo "✅ All checks passed!"
```

### 🔧 Auto-Fix Issues
```bash
cd sdk && python -m black agent_evaluation_sdk/ && python -m ruff check --fix agent_evaluation_sdk/ && echo "✨ Auto-fixes applied!"
```

### Individual Checks

**Format check (Black):**
```bash
cd sdk && python -m black --check agent_evaluation_sdk/
```

**Auto-format:**
```bash
cd sdk && python -m black agent_evaluation_sdk/
```

**Lint check (Ruff):**
```bash
cd sdk && python -m ruff check agent_evaluation_sdk/
```

**Auto-fix linting:**
```bash
cd sdk && python -m ruff check --fix agent_evaluation_sdk/
```

**Type check (MyPy):**
```bash
cd sdk && python -m mypy agent_evaluation_sdk/
```

---

## 🏗️ Terraform Validation

### ✅ Validate Terraform Config
```bash
cd terraform && terraform fmt -recursive && terraform init -backend=false && terraform validate && echo "✅ Terraform valid!"
```

### Format Terraform Files Only
```bash
cd terraform && terraform fmt -recursive
```

---

## 🚀 Complete Pre-Commit Workflow

Run this complete check before committing:

```bash
# 1. Auto-fix SDK issues
cd sdk && python -m black agent_evaluation_sdk/ && python -m ruff check --fix agent_evaluation_sdk/

# 2. Check SDK
cd sdk && python -m black --check agent_evaluation_sdk/ && python -m ruff check agent_evaluation_sdk/ && python -m mypy agent_evaluation_sdk/

# 3. Format and validate Terraform
cd ../terraform && terraform fmt -recursive && terraform validate

# 4. Success!
echo "✅ All checks passed! Ready to commit."
```

---

## 💡 Git Aliases (Optional)

Add these to your `~/.gitconfig`:

```ini
[alias]
    sdk-check = "!cd sdk && python -m black --check agent_evaluation_sdk/ && python -m ruff check agent_evaluation_sdk/ && python -m mypy agent_evaluation_sdk/ && echo '✅ All SDK checks passed!'"
    sdk-fix = "!cd sdk && python -m black agent_evaluation_sdk/ && python -m ruff check --fix agent_evaluation_sdk/ && echo '✨ Auto-fixes applied!'"
    tf-check = "!cd terraform && terraform fmt -check -recursive && terraform validate && echo '✅ Terraform valid!'"
    tf-fix = "!cd terraform && terraform fmt -recursive && echo '✨ Terraform formatted!'"
```

Then use:
```bash
git sdk-check    # Check SDK
git sdk-fix      # Fix SDK issues
git tf-check     # Check Terraform
git tf-fix       # Format Terraform
```

---

## 📦 What Gets Checked in CI/CD

When you push to GitHub, these checks run automatically:

1. **SDK Tests** (`.github/workflows/test-sdk.yml`)
   - Black formatting
   - Ruff linting
   - MyPy type checking
   - Pytest with coverage

2. **Infrastructure Validation** (`.github/workflows/validate-infra.yml`)
   - Terraform format check
   - Terraform init & validate
   - TFLint (warnings only)
   - SDK import compatibility test

---

## 🎯 Quick Tips

- **Always run auto-fix first** before checking (saves time)
- **Check locally before pushing** to catch issues early
- **CI/CD will fail** if any check doesn't pass
- **MyPy type errors** require code changes (can't auto-fix)

---

**Save this file for quick reference!** 📌

