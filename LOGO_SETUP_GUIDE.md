# 🎨 Adding Your EpiScience Logo

Quick guide to add your `episciencelogo.png` to the PubMed Scraper!

---

## 📁 **Folder Structure**

Your project should look like this:

```
your-project/
├── app.py  (or app_multi_keyword.py)
├── pubmed_api_scraper.py
├── requirements.txt
│
├── templates/
│   ├── base_with_logo.html          ← New! Use this instead of base.html
│   ├── index_with_logo.html         ← New! Use this instead of index.html
│   ├── index_multi_with_logo.html   ← New! Use this for multi-keyword
│   ├── results.html
│   ├── results_multi.html
│   └── about.html
│
└── static/
    ├── style.css                     ← Updated with logo styles
    └── images/                       ← CREATE THIS FOLDER!
        └── episciencelogo.png        ← PUT YOUR LOGO HERE!
```

---

## 🚀 **Step-by-Step Setup**

### Step 1: Create the Images Folder

In your project directory:

```bash
# If you already have a static folder:
mkdir static/images

# If you don't have a static folder yet:
mkdir -p static/images
```

### Step 2: Copy Your Logo

Copy `episciencelogo.png` into the `static/images/` folder:

```bash
# Example (adjust path to your logo location):
cp /path/to/your/episciencelogo.png static/images/
```

**Result:**
```
static/
└── images/
    └── episciencelogo.png  ✓
```

### Step 3: Update Your Templates

**Option A: Use the new templates (Recommended)**

Rename or replace your existing templates:

```bash
# For single keyword search:
mv templates/base.html templates/base_old.html
mv templates/index.html templates/index_old.html
cp templates/base_with_logo.html templates/base.html
cp templates/index_with_logo.html templates/index.html

# For multi-keyword search:
cp templates/index_multi.html templates/index_multi.html
```

**Option B: Manual update**

Edit your existing `templates/base.html` and change the nav-brand section:

**Before:**
```html
<div class="nav-brand">
    <i class="fas fa-book-medical"></i>
    <span>PubMed Scraper</span>
</div>
```

**After:**
```html
<div class="nav-brand">
    <img src="{{ url_for('static', filename='images/episciencelogo.png') }}" 
         alt="EpiScience Logo" class="logo-image">
    <span>PubMed Scraper</span>
</div>
```

### Step 4: Update CSS

Your `static/style.css` has been updated with logo styles. Make sure it includes:

```css
.logo-image {
    height: 50px;
    width: auto;
    object-fit: contain;
}

.footer-logo-image {
    height: 40px;
    width: auto;
    object-fit: contain;
    opacity: 0.8;
}

.hero-logo-image {
    height: 80px;
    width: auto;
    object-fit: contain;
}
```

### Step 5: Test It!

```bash
python app.py
# or
python app_multi_keyword.py
```

Open http://localhost:5000 and you should see your logo in:
- ✅ Navigation bar (top)
- ✅ Hero section (center of search page)
- ✅ Footer (bottom)

---

## 🎨 **Logo Placement**

Your logo appears in **3 places**:

### 1. Navigation Bar (Top)
- **Size:** 50px height
- **Position:** Left side, next to "PubMed Scraper" text
- **Visible:** All pages

### 2. Hero Section (Search Page)
- **Size:** 80px height (larger)
- **Position:** Center, above the main title
- **Visible:** Home/search pages only

### 3. Footer (Bottom)
- **Size:** 40px height
- **Position:** Center, above copyright text
- **Visible:** All pages

---

## ⚙️ **Customization Options**

### Adjust Logo Size

Edit `static/style.css`:

```css
/* Navbar logo */
.logo-image {
    height: 60px;  /* Change from 50px to 60px */
}

/* Hero section logo */
.hero-logo-image {
    height: 100px;  /* Change from 80px to 100px */
}

/* Footer logo */
.footer-logo-image {
    height: 50px;  /* Change from 40px to 50px */
}
```

### Remove Logo from Certain Areas

**Don't want logo in hero section?**

Edit `templates/index_with_logo.html` and remove:
```html
<div class="hero-logo">
    <img src="..." alt="..." class="hero-logo-image">
</div>
```

**Don't want logo in footer?**

Edit `templates/base_with_logo.html` and remove the footer logo div.

### Change Logo Position

Edit `static/style.css`:

```css
/* Center the navbar logo */
.nav-brand {
    justify-content: center;  /* Add this */
}

/* Make logo appear on right side */
.navbar .container {
    flex-direction: row-reverse;  /* Add this */
}
```

---

## 🐛 **Troubleshooting**

### Logo Not Showing?

**Check 1: File exists?**
```bash
ls static/images/episciencelogo.png
```

**Check 2: File name is exact?**
- Must be: `episciencelogo.png` (all lowercase)
- Not: `EpiscienceLogo.png` or `episciencelogo.PNG`

**Check 3: Folder structure correct?**
```
static/
└── images/
    └── episciencelogo.png
```
NOT:
```
images/
└── episciencelogo.png
```

**Check 4: Clear browser cache**
- Press `Ctrl+F5` (Windows/Linux)
- Press `Cmd+Shift+R` (Mac)

### Logo Too Big/Small?

Edit the CSS sizes as shown in "Customization Options" above.

### Logo Stretched or Distorted?

The CSS uses `object-fit: contain` which prevents distortion.

If you want it to fill the space:
```css
.logo-image {
    object-fit: cover;  /* Change from 'contain' to 'cover' */
}
```

### Logo Has White Background?

If your logo has a white background and you want transparency:

1. Edit the PNG in an image editor (GIMP, Photoshop, etc.)
2. Remove the white background
3. Save with transparency
4. Replace the file

### Wrong File Path Error?

Make sure you're using:
```python
url_for('static', filename='images/episciencelogo.png')
```

NOT:
```python
url_for('static', filename='episciencelogo.png')  # Wrong!
```

---

## 📋 **Checklist**

- [ ] Created `static/images/` folder
- [ ] Copied `episciencelogo.png` to `static/images/`
- [ ] Updated templates (or renamed new ones)
- [ ] Updated `style.css` with logo styles
- [ ] Tested in browser
- [ ] Logo shows in navbar
- [ ] Logo shows in hero section (if wanted)
- [ ] Logo shows in footer

---

## 🎯 **Quick Commands**

```bash
# Create images folder
mkdir -p static/images

# Copy your logo (adjust source path!)
cp ~/Downloads/episciencelogo.png static/images/

# Check it's there
ls -lh static/images/episciencelogo.png

# Run the app
python app_multi_keyword.py

# Open browser
# Go to http://localhost:5000
```

---

## 📦 **Files You Need**

I've created these updated files for you:

1. **base_with_logo.html** - Base template with logo
2. **index_with_logo.html** - Single search page with logo
3. **index_multi_with_logo.html** - Multi-keyword search page with logo
4. **style.css** - Updated with logo styles

**Download these and place in your project!**

---

## 💡 **Pro Tips**

1. **Logo Format**: PNG with transparency works best
2. **Logo Size**: Recommended at least 200px height for clarity
3. **File Size**: Keep under 100KB for fast loading
4. **Backup**: Keep original logo file separate
5. **Colors**: Logo should contrast with navbar background

---

## 🆘 **Still Need Help?**

If logo still doesn't appear:

1. Check browser console (F12) for errors
2. Verify file permissions: `chmod 644 static/images/episciencelogo.png`
3. Try renaming to a simple name like `logo.png` and update templates
4. Make sure Flask app is restarted after changes

---

**That's it! Your EpiScience logo will now appear throughout the app! 🎉**
