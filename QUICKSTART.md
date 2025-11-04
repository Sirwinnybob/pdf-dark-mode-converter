# Quick Start Guide

## 🚀 Get Running in 3 Steps

### Step 1: Install Dependencies

**Windows:**
```bash
cd backend
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
cd backend
pip3 install -r requirements.txt
```

### Step 2: Start the Server

**Windows:**
```bash
# Simply run the start script
start.bat
```

**Mac/Linux:**
```bash
# Make script executable (first time only)
chmod +x start.sh

# Run it
./start.sh
```

**Or manually:**
```bash
cd backend
python main.py
```

### Step 3: Open the App

1. Open `index.html` in your web browser
2. Drag and drop a PDF or click "Choose PDF File"
3. Select your preferred theme
4. Download your dark mode PDF!

## 🎯 What You'll See

- **Backend Server**: Running on http://localhost:8000
- **API Docs**: Interactive docs at http://localhost:8000/docs
- **Frontend**: Open `index.html` in any modern browser

## ⚡ Quick Test

Want to test immediately? Try this cURL command:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@your-document.pdf" \
  -F "theme=claude" \
  --output dark-mode-output.pdf
```

## 🐳 Using Docker Instead?

```bash
# One command to rule them all
docker-compose up

# Then open index.html in your browser
```

## 🔧 Troubleshooting

### "Connection refused" error
- Make sure the backend server is running on port 8000
- Check the API_URL in index.html matches your server address

### "Module not found" error
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt --force-reinstall
```

### Port 8000 already in use
Edit `backend/main.py` and change:
```python
port = int(os.environ.get("PORT", 8001))  # Changed from 8000
```

## 📚 Next Steps

- Read the full [README_VECTOR.md](README_VECTOR.md) for detailed documentation
- Check the API docs at http://localhost:8000/docs
- Try different themes to see which you prefer!

## 💡 Pro Tips

1. **Theme Preview**: Switch themes on the same PDF without re-uploading
2. **Privacy**: Everything runs locally - no internet required once dependencies are installed
3. **Batch Processing**: Use the API endpoint in scripts for bulk conversion

Happy converting! 🎨
