# Hide My Email Manager - Detailed Usage Guide

## Table of Contents
- [Installation](#installation)
- [First Run](#first-run)
- [Operation Modes](#operation-modes)
- [Search and Filtering](#search-and-filtering)
- [Safety Features](#safety-features)
- [Best Practices](#tips-and-best-practices)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites Check
Before installing, ensure you have:
1. Python 3.8 or higher
2. Google Chrome browser
3. Active iCloud account with Hide My Email enabled

### Step-by-Step Installation

#### Windows
```powershell
# 1. Clone the repository
git clone https://github.com/lukenmorris/icloud-hide-my-email-manager.git
cd icloud-hide-my-email-manager

# 2. Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the script
python run.py
```

#### macOS/Linux
```bash
# 1. Clone the repository
git clone https://github.com/lukenmorris/icloud-hide-my-email-manager.git
cd icloud-hide-my-email-manager

# 2. Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip3 install -r requirements.txt

# 4. Run the script
python3 run.py
```

## First Run

### 1. Starting the Script
When you run the script for the first time:
```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🔐 iCloud Hide My Email Manager                          ║
║                                                              ║
║     Automate your iCloud Hide My Email addresses            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🔍 Running system checks...
✅ Python version OK
✅ Chrome check complete
✅ All requirements satisfied
```

### 2. Chrome Browser Opens
- Chrome will open automatically
- Navigate to iCloud sign-in page
- **Important**: The script waits for you to complete login

### 3. Sign In to iCloud
1. Enter your Apple ID
2. Enter your password
3. Complete 2FA if enabled
4. Wait for iCloud+ page to load

### 4. Headless Mode Option
After successful login, you'll be asked:
```
==================================================
HEADLESS MODE OPTION
==================================================
Would you like to switch to headless mode? (yes/no):
```
- **Yes**: Browser runs in background (less distracting)
- **No**: Browser stays visible (recommended for first time)

## Operation Modes

### Preview Mode (Recommended First)
Perfect for exploring your emails without making changes:
```
Select a mode:
4. Preview mode (view emails without changes)

Which emails would you like to preview?
1. Active emails
2. Inactive emails
3. Both

Do you want to filter by a search term? (yes/no): no
```

Output shows:
- Email addresses
- Associated labels/notes
- Summary statistics by service
- Summary by label

### Deactivate Mode
Disables active email addresses (reversible):
```
Select a mode:
1. Deactivate active emails

Do you want to filter by a specific search term? (yes/no): yes
Enter search term: amazon
```

Process:
1. Shows preview of affected emails
2. Asks for confirmation
3. Processes emails one by one
4. Shows progress and time estimates

### Delete Mode
Permanently removes inactive emails:
```
Select a mode:
2. Permanently delete inactive emails

⚠️ WARNING: This action is PERMANENT!
```

Safety features:
- Only works on inactive emails
- Shows detailed preview
- Requires explicit confirmation
- Cannot be undone

### Purge Mode (Use with Extreme Caution)
Combines deactivate and delete:
```
Select a mode:
3. Purge mode (deactivate then delete)

⚠️⚠️⚠️ EXTREME WARNING ⚠️⚠️⚠️
This will:
1. Deactivate ALL active Hide My Email addresses
2. Permanently DELETE ALL Hide My Email addresses
This is IRREVERSIBLE!
```

## Search and Filtering

### How Search Works
- Searches both email addresses AND labels/notes
- Case-insensitive matching
- Partial matches work

### Search Examples

#### By Service
```
Enter search term: amazon
# Finds: shopping.amazon@icloud.com, deals.amazon@icloud.com
```

#### By Label
```
Enter search term: newsletter
# Finds all emails with "newsletter" in their label
```

#### By Domain Pattern
```
Enter search term: shop
# Finds: shop.target@icloud.com, shopping.amazon@icloud.com
```

## Safety Features

### Multiple Confirmation Levels

1. **Mode Selection** - Choose operation type
2. **Search Filter** - Optional filtering
3. **Preview** - See exactly what will be affected
4. **Final Confirmation** - Last chance to cancel
5. **Progress Tracking** - Monitor operations in real-time

### Interruption Handling
- Press `Ctrl+C` to safely stop at any time
- Script cleanly exits without corrupting state
- Processed emails are marked as complete

### Preview Before Action
Every destructive operation shows:
```
============================================================
⚠️  OPERATION PREVIEW
============================================================
📋 Emails to be deactivated: 47 total
🔍 Filter applied: 'amazon'

  1. random.amazon@icloud.com → Amazon Order #123
  2. deals.amazon@icloud.com → Amazon Prime Deals
  ...

⚠️  FINAL CONFIRMATION REQUIRED ⚠️
Do you want to proceed? (yes/no):
```

## Best Practices

### Before You Start
1. **Always use Preview Mode first** to understand your email structure
2. **Start with search filters** to target specific services
3. **Test with a small batch** before bulk operations

### Recommended Workflow
1. Preview all emails to understand what you have
2. Identify services you want to remove
3. Use search to filter those services
4. Preview the filtered results
5. Proceed with deactivation/deletion

### Performance Tips
- **Headless mode** is ~10% faster
- Expect ~20 emails/minute processing rate
- Large operations (100+ emails) may take significant time
- Script shows time estimates for planning

## Troubleshooting

### Common Issues and Solutions

#### Chrome Driver Issues
```
Error: Chrome driver not found
```
**Solution**: The script auto-downloads drivers, but you can manually update:
```bash
pip install --upgrade webdriver-manager
```

#### Login Timeout
```
Error: Timeout waiting for iCloud+ page
```
**Solutions**:
- Check internet connection
- Disable browser extensions
- Try incognito mode
- Ensure 2FA is properly configured

#### Element Not Found
```
Error: Unable to locate element
```
**Solutions**:
- Ensure you're on the iCloud+ features page
- Refresh the page and restart script
- Check Hide My Email is enabled in your account

#### Search Not Working
```
No emails found matching 'searchterm'
```
**Solutions**:
- Check spelling
- Try partial matches
- Search is case-insensitive

### Advanced Troubleshooting

#### Enable Debug Mode
Add to your script for verbose output:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Manual Chrome Profile
Use existing Chrome profile with saved login:
```python
chrome_options.add_argument(f"user-data-dir={profile_path}")
```

#### Slow Performance
- Close other Chrome windows
- Disable unnecessary browser extensions
- Use headless mode after login
- Check system resources

### Getting Help

If you encounter issues:

1. **Check existing issues**: [GitHub Issues](https://github.com/lukenmorris/icloud-hide-my-email-manager/issues)
2. **Create new issue** with:
   - Python version (`python --version`)
   - Error message
   - Steps to reproduce
3. **Join discussion**: [GitHub Discussions](https://github.com/lukenmorris/icloud-hide-my-email-manager/discussions)

## DOs and DONTs

✅ **DO**:
- Always preview before acting
- Use search filters for targeted operations
- Keep backups of important email addresses
- Run in small batches initially
- Monitor progress carefully

❌ **DON'T**:
- Run purge mode without careful consideration
- Ignore confirmation prompts
- Run on shared computers without permission
- Delete emails you might need later
- Run multiple instances simultaneously

---

Remember: **Deleted emails cannot be recovered!** Always use preview mode first and carefully review what will be deleted.