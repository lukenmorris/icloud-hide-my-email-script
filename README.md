# iCloud Hide My Email Manager

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/powered%20by-Selenium-43B02A.svg)](https://www.selenium.dev/)

Automate the management of your iCloud Hide My Email addresses - deactivate, delete, and organize in bulk with safety and ease.

## ✨ Features

- 🔍 **Preview Mode** - See exactly what will be affected before making any changes
- 🎯 **Smart Filtering** - Search by email address or label/note
- 🚀 **Bulk Operations** - Process hundreds of emails automatically
- 📊 **Progress Tracking** - Real-time progress with time estimates
- 🔒 **Safety First** - Multiple confirmations for destructive actions
- 👻 **Headless Mode** - Run in background after login
- 🏷️ **Label Support** - View and filter by email labels/notes

## 🚀 Quick Start

### Option 1: Use pip and pyproject.toml (Recommended)
```bash
# Update pip
python -m pip install --upgrade pip

# Install the tool directly from GitHub
pip install git+https://github.com/lukenmorris/icloud-hide-my-email-manager.git
```

### Option 2: Clone and Run
```bash
# Clone the repository
git clone https://github.com/lukenmorris/icloud-hide-my-email-manager.git
cd icloud-hide-my-email-manager

# Install dependencies
pip install -r requirements.txt

# Run the script
python run.py
```

## 📋 Prerequisites

- **Python 3.8** or higher ([Download Python](https://www.python.org/downloads/))
- **Google Chrome** browser ([Download Chrome](https://www.google.com/chrome/))
- **iCloud account** with Hide My Email enabled
- **Windows 10/11**, **macOS 10.14+**, or **Linux**

## 🎮 Usage

### Starting the Script

1. **Run the script:**
   ```bash
   # If installed via Option 1
   hide-my-email

   # If installed via Option 2
   python run.py
   ```

2. **Chrome will open automatically** - Sign in to your iCloud account when prompted

3. **Choose optional headless mode** after login for background operation

4. **Select your operation mode:**

### Operation Modes

#### 🔍 Preview Mode
View your emails without making any changes. Perfect for exploring what you have.
- Filter by search terms
- View labels and notes
- See summary statistics

#### ⚡ Deactivate Mode
Deactivate active Hide My Email addresses (they can be reactivated later).
- Addresses stop receiving emails
- Can be reactivated anytime
- Safer than deletion

#### 🗑️ Delete Mode
Permanently delete inactive email addresses.
- **Cannot be undone**
- Only works on already inactive emails
- Multiple confirmations required

#### 💣 Purge Mode
Complete cleanup - deactivates active emails then deletes them.
- Combines deactivate and delete
- **Permanent and irreversible**
- Extra confirmations required

### Search Filtering

All modes support search filtering:
- Searches both email addresses and labels/notes
- Case-insensitive
- Example: searching "amazon" finds all Amazon-related emails

### Safety Features

- **Preview before action** - See exactly what will be affected
- **Multiple confirmations** - No accidental deletions
- **Progress tracking** - Know what's happening at all times
- **Graceful interruption** - Ctrl+C safely stops the script

## 📸 Screenshots

<details>
<summary>View Screenshots</summary>

### Main Menu
```
Select a mode:
1. Deactivate active emails
2. Permanently delete inactive emails
3. Purge mode (deactivate then delete)
4. Preview mode (view emails without changes)
5. Exit
Enter choice (1, 2, 3, 4, or 5):
```

### Preview Mode Example
```
==================================================
📧 ACTIVE EMAILS
==================================================
Found 47 active emails matching 'Target' (Total active: 234)

Displaying 47 active emails:
--------------------------------------------------------------------------------
  1. random.target@icloud.com                      → Target Order #12345
  2. another.target@icloud.com                     → Target Promo Newsletter
  3. shopping.target@icloud.com                    → Target RedCard Account
...
--------------------------------------------------------------------------------

📊 Summary by service:
   • target: 47 emails

🏷️  Summary by label:
   • Target Order: 23 emails
   • Target Promo Newsletter: 15 emails
   • Target RedCard Account: 9 emails
```

### Operation Progress
```
Starting Deactivation process...

Remaining active emails matching 'Target': 43 (Total active: 234)
Progress: 4/47 (8.5%) | Elapsed: 12 seconds | ETA: 2.1 minutes

Processing: random.target@icloud.com → Target Order #12345
--> Deactivating random.target@icloud.com (Label: Target Order #12345)...
✅ Successfully deactivated email #5: random.target@icloud.com
   📊 Rate: 15.2 emails/minute
```

</details>

## ⚙️ Advanced Options

### Headless Mode
After login, you can switch to headless mode to run the browser in the background:
- Less distracting
- Slightly faster performance
- Still shows progress in terminal

### Batch Processing
The script handles large batches efficiently:
- Processes ~20 emails per minute
- Automatic rate limiting to prevent issues
- Time estimates for operations

## 🛠️ Troubleshooting

<details>
<summary>Common Issues</summary>

### Chrome Driver Issues
If you see Chrome driver errors:
```bash
# The script auto-downloads drivers, but you can manually update:
pip install --upgrade webdriver-manager
```

### Login Timeout
If login times out after 5 minutes:
- Check your internet connection
- Try disabling browser extensions
- Ensure 2FA is properly configured

### Elements Not Found
If the script can't find elements:
- Make sure you're on the iCloud+ features page
- Try refreshing the page
- Check that Hide My Email is enabled on your account

</details>

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is not affiliated with Apple Inc. Use at your own risk. Always use preview mode first and carefully review what will be deleted before confirming any destructive operations.

## 🙏 Acknowledgments

- Built with [Selenium WebDriver](https://www.selenium.dev/)
- Chrome driver management by [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager)
- Inspired by the need to manage hundreds of Hide My Email addresses

## 📧 Support

- 🐛 [Report Issues](https://github.com/lukenmorris/icloud-hide-my-email-manager/issues)
- 💬 [Discussions](https://github.com/lukenmorris/icloud-hide-my-email-manager/discussions)
- ⭐ Star this repo if you find it useful!

---

**Note:** Remember to always preview your changes before executing any destructive operations. Your email addresses cannot be recovered once deleted!