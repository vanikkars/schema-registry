# Contract Folders Structure

This directory contains data contract definitions organized into two main folders:

## 📁 Folder Structure

```
contracts/
├── current/              ← ACTIVE CONTRACTS (Used by GitHub Actions)
│   ├── transaction/
│   │   └── transaction_v1.json
│   └── user/
│       └── user_v1.json
│
├── all/                  ← ALL CONTRACT VERSIONS (Archive/Reference)
│   ├── transaction/
│   │   ├── 01/
│   │   │   └── transaction_v1.json
│   │   └── 02/
│   │       └── transaction_v1.json
│   ├── user/
│   │   ├── 01/
│   │   │   └── user_v1.json
│   │   └── 02/
│   │       └── user_v1.json
│   └── test_contract.json
│
└── README.md             ← This file
```

## 🎯 Purpose of Each Folder

### `contracts/current/`

**Active contracts currently in use.**

- Contains the latest/active versions of all contracts
- **This is what GitHub Actions validates and validates in PRs**
- When you change contracts here, GitHub Actions automatically validates them
- Keep this folder lean with only current contracts

**Usage:**
```bash
# Validate current contracts
make validate-contracts

# Create PR with changes to current/ folder
git checkout -b update-user-contract
# Modify contracts/current/user/user_v1.json
git push origin update-user-contract
# Open PR → GitHub Actions validates automatically ✅
```

### `contracts/all/`

**Archive of all contract versions.**

- Contains every version of every contract (01, 02, etc.)
- Used for reference and historical tracking
- GitHub Actions does NOT validate changes here
- Safe for storing historical versions

**Usage:**
```bash
# Validate all versions (for reference only)
make validate-contracts-all

# View historical versions
ls contracts/all/user/01/    # Version 1
ls contracts/all/user/02/    # Version 2
```

## 📝 How to Update Contracts

### To Update a Contract

1. **Edit the contract** in `contracts/current/`:
   ```bash
   # Example: Update user contract
   nano contracts/current/user/user_v1.json
   ```

2. **Test locally**:
   ```bash
   make validate-contracts
   ```

3. **Commit and push**:
   ```bash
   git checkout -b update-user-contract
   git add contracts/current/
   git commit -m "chore: update user contract"
   git push origin update-user-contract
   ```

4. **Open PR on GitHub**
   - GitHub Actions triggers automatically
   - Validates your changes
   - Auto-merges if valid ✅

### To Archive a Version

When you create a new version:

1. **Copy current to `all/`** with new version number:
   ```bash
   # If updating user contract to v2
   mkdir -p contracts/all/user/02
   cp contracts/current/user/user_v1.json contracts/all/user/02/
   ```

2. **Update current** with new version:
   ```bash
   # Update contracts/current/user/user_v1.json with new changes
   ```

3. **Commit both**:
   ```bash
   git add contracts/current/ contracts/all/
   git commit -m "chore: add user contract v2 to archive"
   ```

## 🔄 GitHub Actions Behavior

**GitHub Actions only validates contracts from `contracts/current/`**

| Folder | Validated by GitHub Actions? |
|--------|------------------------------|
| `contracts/current/` | ✅ YES - Will auto-merge if valid |
| `contracts/all/` | ❌ NO - Changes ignored |

This means:
- ✅ Only production-ready contracts in `current/`
- ✅ Automatic validation for important changes
- ❌ Archive changes won't trigger workflow
- ✅ Safe to experiment in `all/` folder

## 📊 Makefile Commands

```bash
# Validate current contracts (used by GitHub Actions)
make validate-contracts

# Validate all contracts (archive reference)
make validate-contracts-all

# Export validation results
make validate-export           # Current only
make validate-export-all       # All versions

# Test against remote API
make validate-remote           # Current only
```

## 🗂️ File Organization Best Practices

### ✅ DO

- Keep `current/` folder clean with only active contracts
- Archive old versions in `all/` with version numbers
- Use semantic versioning (01, 02, 03, etc.) in `all/`
- Document changes in commit messages

### ❌ DON'T

- Don't put experimental contracts in `current/` folder
- Don't delete old versions from `all/` (keep for reference)
- Don't modify `all/` folder in PRs (not validated)
- Don't use `all/` for production contracts

## 💡 Examples

### Example 1: Update User Contract

```bash
# 1. Edit current version
nano contracts/current/user/user_v1.json

# 2. Test locally
make validate-contracts

# 3. Archive old version (if it's a breaking change)
mkdir -p contracts/all/user/03
cp contracts/all/user/02/user_v1.json contracts/all/user/03/

# 4. Push
git add contracts/current/ contracts/all/
git commit -m "feat: add email to user contract (v3)"
git push origin update-user-contract

# 5. Create PR → Auto-merges ✅
```

### Example 2: Check Historical Versions

```bash
# View all user contract versions
ls -la contracts/all/user/

# Compare versions
diff contracts/all/user/01/user_v1.json contracts/all/user/02/user_v1.json

# Validate all versions (for reference)
make validate-contracts-all
```

### Example 3: Add New Contract

```bash
# 1. Create in current folder
mkdir -p contracts/current/order
cat > contracts/current/order/order_v1.json << 'EOF'
{
  "name": "order-v1",
  "namespace": "com.example.data",
  "type": "record",
  "fields": [
    {"name": "order_id", "type": "string"},
    {"name": "customer_id", "type": "string"}
  ]
}
EOF

# 2. Test locally
make validate-contracts

# 3. Push and create PR
git add contracts/current/
git commit -m "feat: add order contract"
git push origin add-order-contract

# 4. GitHub Actions validates → Auto-merges ✅
```

## 📖 Related Documentation

- [CONTRACT_AUTOMATION_README.md](../CONTRACT_AUTOMATION_README.md) - Overview of automation
- [CONTRACT_AUTOMATION_QUICKSTART.md](../CONTRACT_AUTOMATION_QUICKSTART.md) - Setup guide
- [docs/NGROK_SETUP.md](../docs/NGROK_SETUP.md) - How to expose local API

## ❓ FAQ

**Q: Why two folders?**
A: `current/` for production contracts (GitHub Actions validates), `all/` for historical versions and reference.

**Q: Will GitHub Actions validate changes to `contracts/all/`?**
A: No, GitHub Actions only watches `contracts/current/`.

**Q: Can I delete old versions from `all/`?**
A: You can, but recommended to keep them for historical reference.

**Q: Do I need to keep `current/` and `all/` in sync?**
A: No, `all/` is just for archiving. `current/` is what matters.

**Q: What if I want to revert to an old version?**
A: Copy from `contracts/all/old_version/` to `contracts/current/` and create a PR.

## 🔗 Workflow

```
Developer makes changes
        ↓
Edits contracts/current/ → GitHub Actions triggers ✅
Edits contracts/all/     → GitHub Actions ignores ❌
        ↓
If current/ changed:
  - Validates contract
  - Posts results to PR
  - Auto-merges if valid
        ↓
Archive versions in contracts/all/ manually
```