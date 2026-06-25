# Pushing Codebase to GitHub

This guide outlines how to initialize Git version control and push the Worldwide Food Scanner codebase (including both the Flask backend and the Flutter mobile app) to a remote **GitHub** repository.

---

## Step-by-Step Push Instructions

### 1. Initialize Git & Check Ignored Files
We have pre-configured a [.gitignore](file:///c:/food-product-scanner-main/.gitignore) file in the root folder to prevent tracking system caches, local environment keys (`.env`), and temporary logs.

Initialize a new local repository:
```bash
git init
```

### 2. Stage All Project Files
Stage all tracked files (both Flask server files and the new `food_scanner_mobile/` Flutter code):
```bash
git add .
```

To verify which files are staged for commit, run:
```bash
git status
```

### 3. Create the First Commit
```bash
git commit -m "Initial commit of Worldwide Food Scanner App (Flask Backend + Flutter Mobile Frontend)"
```

### 4. Create a New Repository on GitHub
1. Log in to [GitHub](https://github.com/).
2. Click the **"+"** icon in the upper right and select **New repository**.
3. Name your repository (e.g. `worldwide-food-scanner`).
4. Keep the checkbox for **Initialize this repository with a README** unchecked (since you already have local README files).
5. Click **Create repository**.

### 5. Link Local Repository & Push
Copy the Git URL from the repository setup page and run:
```bash
# Rename active branch to 'main'
git branch -M main

# Link your local repo to GitHub
git remote add origin https://github.com/YOUR_USERNAME/worldwide-food-scanner.git

# Push the codebase to GitHub
git push -u origin main
```
