# 🔧 Install Git - Step by Step Guide

## Problem
```
git : The term 'git' is not recognized...
```

This means Git is not installed on your computer.

---

## ✅ Solution: Install Git

### Method 1: Download Git for Windows (Recommended)

1. **Download Git**
   - Go to: https://git-scm.com/download/win
   - Click "Click here to download" (64-bit version)
   - File will be named: `Git-2.43.0-64-bit.exe` (or similar)

2. **Run the Installer**
   - Double-click the downloaded file
   - Click "Next" through the installation
   - **Important settings:**
     - ✅ Use Git from the Windows Command Prompt
     - ✅ Use the OpenSSL library
     - ✅ Checkout Windows-style, commit Unix-style line endings
     - ✅ Use MinTTY (default terminal)
     - ✅ Enable file system caching

3. **Complete Installation**
   - Click "Install"
   - Wait for installation to complete
   - Click "Finish"

4. **Verify Installation**
   - **Close and reopen PowerShell** (important!)
   - Run:
     ```bash
     git --version
     ```
   - Should show: `git version 2.43.0` (or similar)

---

## 🎯 After Installing Git

### Configure Git (First Time)

```bash
# Set your name
git config --global user.name "Your Name"

# Set your email
git config --global user.email "your.email@example.com"

# Verify
git config --list
```

### Then Push to GitHub

```bash
# 1. Initialize Git
git init

# 2. Add files
git add .

# 3. Commit
git commit -m "Initial commit: Food Product Scanner with Gemini AI"

# 4. Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/food-product-scanner.git

# 5. Push
git branch -M main
git push -u origin main
```

---

## 🚀 Alternative: Use GitHub Desktop (No Git Installation Needed)

If you prefer a GUI instead of command line:

### 1. Download GitHub Desktop
- Go to: https://desktop.github.com/
- Click "Download for Windows"
- Install the application

### 2. Sign In
- Open GitHub Desktop
- Sign in with your GitHub account

### 3. Add Your Project
- File → Add Local Repository
- Browse to: `C:\Users\MADAN\OneDrive\New folder`
- Click "Add Repository"

### 4. Create Repository on GitHub
- Click "Publish repository"
- Name: `food-product-scanner`
- Description: `AI-powered food product scanner`
- Choose Public or Private
- **Uncheck** "Keep this code private" if you want it public
- Click "Publish repository"

### 5. Done!
Your project is now on GitHub!

---

## 📋 Quick Comparison

### Git Command Line:
✅ More control
✅ Faster for experienced users
✅ Works everywhere
❌ Requires learning commands

### GitHub Desktop:
✅ Easy to use
✅ Visual interface
✅ No commands to remember
❌ Less control
❌ Windows/Mac only

---

## 🔍 Troubleshooting

### Problem: Git still not recognized after install
**Solution:**
1. Close PowerShell completely
2. Reopen PowerShell
3. Try `git --version` again

### Problem: PATH not updated
**Solution:**
1. Search for "Environment Variables" in Windows
2. Click "Edit the system environment variables"
3. Click "Environment Variables"
4. Under "System variables", find "Path"
5. Click "Edit"
6. Add: `C:\Program Files\Git\cmd`
7. Click OK
8. Restart PowerShell

### Problem: Installation failed
**Solution:**
- Run installer as Administrator
- Right-click installer → "Run as administrator"

---

## ✅ Verification Checklist

After installation:

- [ ] Git installed
- [ ] PowerShell restarted
- [ ] `git --version` works
- [ ] Git configured (name and email)
- [ ] Ready to push to GitHub

---

## 🎯 Next Steps

Once Git is installed:

1. **Configure Git** (name and email)
2. **Create GitHub account** (if you don't have one)
3. **Create repository** on GitHub
4. **Push your project**

See `GITHUB_PUSH_GUIDE.md` for detailed instructions.

---

## 📞 Download Links

- **Git for Windows**: https://git-scm.com/download/win
- **GitHub Desktop**: https://desktop.github.com/
- **GitHub Account**: https://github.com/signup

---

**Choose your preferred method and get started!** 🚀

*Last Updated: January 7, 2026*
