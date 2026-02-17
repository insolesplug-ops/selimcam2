# 🚀 How to Push to GitHub

## Step 1: Create a GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. **Repository name**: `FINALMAINCAMMM` (or your preferred name)
3. **Description**: "Professional camera app for Raspberry Pi 3 A+ with standby mode"
4. **Public** or **Private** (your choice)
5. **DO NOT** check "Initialize with README" (we have one already)
6. Click "Create repository"

---

## Step 2: Initialize Git Locally

```bash
cd /Users/selimgun/Downloads/FINALMAINCAMMM

# Initialize git repo
git init

# Set your name and email (GitHub account)
git config user.name "Your Name"
git config user.email "your.email@github.com"

# Global config (optional, applies to all repos)
# git config --global user.name "Your Name"
# git config --global user.email "your.email@github.com"
```

---

## Step 3: Add All Files to Git

```bash
cd /Users/selimgun/Downloads/FINALMAINCAMMM

# Add everything
git add .

# Check what will be pushed
git status

# Expected output: All files green, marked as "new file"
```

---

## Step 4: Create First Commit

```bash
git commit -m "Initial commit: SelimCam v2.0 - Production camera app for Pi 3 A+"
```

---

## Step 5: Connect to GitHub

```bash
# Replace YOUR_USERNAME with your actual GitHub username!
git remote add origin https://github.com/YOUR_USERNAME/FINALMAINCAMMM.git

# Verify connection
git remote -v
```

---

## Step 6: Push to GitHub

```bash
# Rename branch to "main" (GitHub standard)
git branch -M main

# Push to GitHub
git push -u origin main

# First time might ask for GitHub credentials
# You may need to use: Personal Access Token instead of password
# See: https://github.com/settings/tokens
```

---

## ✅ That's It!

Your code is now on GitHub at:
```
https://github.com/YOUR_USERNAME/FINALMAINCAMMM
```

---

## 🔄 Regular Updates (After Making Changes)

```bash
# 1. Check what changed
git status

# 2. Add changes
git add .

# 3. Commit with message
git commit -m "Your message describing the change"

# 4. Push to GitHub
git push
```

---

## 📝 Good Commit Messages

```bash
# Good examples:
git commit -m "Add cool boot animation with orbiting dots"
git commit -m "Fix /home/pi path detection for simulator"
git commit -m "Improve power management on Pi 3 A+"
git commit -m "Add quiet mode for production deployment"

# Avoid:
git commit -m "fix"
git commit -m "update"
git commit -m "changes"
```

---

## 🆘 Troubleshooting

### Error: "fatal: not a git repository"
```bash
# Make sure you're in the right directory
cd /Users/selimgun/Downloads/FINALMAINCAMMM
git status
```

### Error: "Could not resolve host: github.com"
```bash
# Check internet connection
# Or try SSH instead of HTTPS:
git remote set-url origin git@github.com:YOUR_USERNAME/FINALMAINCAMMM.git
```

### Error: "Permission denied (publickey)"
```bash
# You need to set up SSH key or use Personal Access Token
# See: https://github.com/settings/keys
# Or use HTTPS with PAT: https://github.com/settings/tokens
```

### Want to undo last commit?
```bash
git reset --soft HEAD~1  # Keep changes
git reset --hard HEAD~1  # Discard changes
```

---

## 🔐 Using Personal Access Token (Recommended)

Instead of password, GitHub uses tokens now:

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: `SelimCam Upload`
4. Grant: `repo` scope (full control of private repositories)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

Then use it like a password:
```bash
git push
# Username: YOUR_USERNAME
# Password: paste_the_token_here
```

Or use it in the URL:
```bash
git remote set-url origin https://YOUR_USERNAME:TOKEN@github.com/YOUR_USERNAME/FINALMAINCAMMM.git
git push
```

---

## 📊 What Gets Uploaded

✅ **Uploaded**:
- All Python code (.py files)
- Configuration (config.json)
- Documentation (README.md, *.md files)
- Requirements (requirements.txt)
- Service files (selimcam.service, start_camera.sh)
- Assets (fonts, images)

❌ **NOT Uploaded** (because of .gitignore):
- Virtual environment (.venv/)
- Python cache (__pycache__/)
- Log files
- Saved photos (camera_app_data/photos/)

---

## 💡 Pro Tips

### Keep repo clean
```bash
# Before pushing, check what you're uploading
git status
git diff --cached
```

### Create branches for features
```bash
# Create feature branch
git checkout -b feature/cool-new-feature

# Make changes, commit
git add .
git commit -m "Add cool new feature"

# Push branch
git push -u origin feature/cool-new-feature

# Later, merge back to main on GitHub (create Pull Request)
```

### View commit history
```bash
git log --oneline -10  # Last 10 commits
git log --graph --pretty=format:'%h - %s'
```

---

## 📚 Next Steps

- ⭐ Star your own repo (optional)
- 📎 Add GitHub topics: `raspberry-pi`, `camera-app`, `python`
- 📖 Pin important issues
- 🤝 Enable "Discussions" for user feedback
- 🔔 Watch for stars and forks!

---

**Ready to upload?**

```bash
cd /Users/selimgun/Downloads/FINALMAINCAMMM
git status
git push
```

Good luck! 🚀
