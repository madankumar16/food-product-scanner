@echo off
echo ========================================
echo Food Product Scanner - GitHub Push
echo ========================================
echo.

echo Step 1: Initializing Git Repository...
git init
echo.

echo Step 2: Adding files...
git add .
echo.

echo Step 3: Creating first commit...
git commit -m "Initial commit: Food Product Scanner with Gemini AI"
echo.

echo Step 4: Setting up remote...
echo Please enter your GitHub username:
set /p username="Username: "
echo.

git remote add origin https://github.com/%username%/food-product-scanner.git
echo.

echo Step 5: Pushing to GitHub...
git branch -M main
git push -u origin main
echo.

echo ========================================
echo Done! Check your GitHub repository:
echo https://github.com/%username%/food-product-scanner
echo ========================================
pause
