# PDF Dark Mode Converter - Vector Edition

A next-generation PDF dark mode converter that **preserves vector data** for crystal-clear text and searchable documents. Unlike traditional approaches that rasterize PDFs, this tool manipulates PDF content streams directly to transform colors while maintaining full vector quality.

## ✨ Key Features

- **🎯 True Vector Preservation**: Manipulates PDF content streams directly - no rasterization
- **📝 Text Searchability**: All text remains selectable and searchable
- **🔍 Crystal Clear Quality**: No jagged edges or quality loss
- **📦 Smaller File Sizes**: Vector data is more compact than rasterized images
- **🎨 Multiple Themes**: 6 carefully crafted dark mode themes
- **🔒 Privacy-Focused**: Can run completely locally - your documents stay on your machine
- **⚡ Fast Processing**: Efficient content stream manipulation

## 🎨 Available Themes

1. **True Black (Classic)** - Pure black background (0, 0, 0)
2. **Claude Warm** - Warm dark brown (42, 37, 34)
3. **ChatGPT Cool** - Cool dark gray-blue (52, 53, 65)
4. **Sepia Dark** - Dark sepia tone (40, 35, 25)
5. **Midnight Blue** - Deep blue (25, 30, 45)
6. **Forest Green** - Dark green (25, 35, 30)

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **PyMuPDF (fitz)** for PDF content stream manipulation
- **FastAPI** for REST API endpoints
- **Pillow** for embedded image transformation
- Direct PDF operator parsing and color transformation

### Frontend (HTML + JavaScript)
- Single-page web interface
- PDF.js for preview rendering
- Drag-and-drop file support
- Real-time progress indication

## 📋 Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) Docker for containerized deployment

## 🚀 Quick Start

### Option 1: Local Python Installation

1. **Clone the repository**
   ```bash
   cd pdf-dark-mode-converter
   ```

2. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Start the backend server**
   ```bash
   python main.py
   ```

   The API will start on `http://localhost:8000`

4. **Open the frontend**
   - Open `index.html` in your web browser
   - Or serve it with a local server:
     ```bash
     # Python
     python -m http.server 3000

     # Node.js
     npx serve .
     ```

5. **Upload a PDF and convert!**

### Option 2: Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Access the application**
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - Open `index.html` in your browser

### Option 3: Docker Manual Build

```bash
# Build the image
docker build -t pdf-dark-mode-converter .

# Run the container
docker run -p 8000:8000 pdf-dark-mode-converter
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/main.py` to change:
- **Port**: Set `PORT` environment variable or modify the default (8000)
- **CORS**: Update `allow_origins` in the CORS middleware for production

### Frontend Configuration

Edit `index.html` to change:
- **API URL**: Update `API_URL` constant (line ~200) to point to your backend
  ```javascript
  const API_URL = 'http://localhost:8000';  // Change for production
  ```

## 📡 API Documentation

### Endpoints

#### `GET /`
Health check endpoint

**Response:**
```json
{
  "status": "ok",
  "message": "PDF Dark Mode Converter API is running",
  "version": "2.0.0",
  "features": ["vector-preservation", "text-searchability", "multiple-themes"]
}
```

#### `POST /convert`
Convert a PDF to dark mode

**Parameters:**
- `file` (multipart/form-data): PDF file to convert
- `theme` (form field): Theme name (classic, claude, chatgpt, sepia, midnight, forest)

**Response:** Binary PDF file

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.pdf" \
  -F "theme=claude" \
  --output document_dark.pdf
```

#### `GET /themes`
Get available themes

**Response:**
```json
{
  "themes": [
    {
      "id": "classic",
      "name": "True Black (Classic Inversion)",
      "background": {"r": 0, "g": 0, "b": 0}
    },
    ...
  ]
}
```

### Interactive API Docs

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## 🔬 How It Works

### Vector-Based Processing

Unlike the original rasterization approach, this version:

1. **Parses PDF Content Streams**: Extracts the raw PDF drawing commands
2. **Identifies Color Operators**: Finds all color-setting operators:
   - `rg/RG`: RGB colors (non-stroking/stroking)
   - `g/G`: Grayscale colors
   - `k/K`: CMYK colors
3. **Transforms Colors**: Applies dark mode transformations:
   - Light backgrounds (brightness > 0.96) → Theme background color
   - Dark content → Brightened using HSV adjustment
   - Preserves color relationships and hue
4. **Reconstructs Content Stream**: Rebuilds the PDF with modified colors
5. **Handles Embedded Images**: Separately transforms raster images at pixel level
6. **Preserves Everything Else**: Fonts, text encoding, paths, and vector data remain intact

### Color Transformation Algorithm

```python
# Pseudo-code
if brightness(color) > 0.96:
    # Background detection
    return theme_background_color
else:
    # Content brightening
    hsv = rgb_to_hsv(color)
    if hsv.v < 0.5:
        hsv.v = 0.4 + hsv.v * 0.6  # Brighten dark colors
    return hsv_to_rgb(hsv)
```

## 📊 Comparison: Raster vs Vector

| Feature | Old (Raster) | New (Vector) |
|---------|--------------|--------------|
| Text Quality | Pixelated | Perfect |
| Searchable Text | ❌ No | ✅ Yes |
| File Size | Large | Small |
| Processing Speed | Slow | Fast |
| Vector Graphics | Lost | Preserved |
| Font Rendering | Blurry | Sharp |

## 🛠️ Development

### Project Structure

```
pdf-dark-mode-converter/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── pdf_processor.py     # PyMuPDF vector processing engine
│   └── requirements.txt     # Python dependencies
├── index.html               # Frontend web interface
├── img/                     # Static assets
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
└── README_VECTOR.md        # This file
```

### Adding New Themes

1. **Backend**: Add theme to `pdf_processor.py`:
   ```python
   self.themes = {
       # ... existing themes ...
       "mytheme": {"r": 30, "g": 30, "b": 40}
   }
   ```

2. **Frontend**: Add option to `index.html`:
   ```html
   <option value="mytheme">My Custom Theme</option>
   ```

3. **Update API docs**: Add to `main.py` `/themes` endpoint

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when test suite is added)
pytest tests/
```

## 🚢 Deployment

### Production Deployment Options

#### 1. Cloud Platforms

**Heroku:**
```bash
heroku create your-pdf-converter
heroku container:push web
heroku container:release web
```

**Railway.app:**
- Connect your GitHub repository
- Railway auto-detects Dockerfile
- Set environment variables if needed

**Render:**
- Create new Web Service
- Connect repository
- Select "Docker" environment
- Deploy

#### 2. VPS Deployment

```bash
# On your server
git clone <your-repo>
cd pdf-dark-mode-converter
docker-compose up -d

# Set up nginx reverse proxy
sudo nano /etc/nginx/sites-available/pdf-converter
```

**Nginx config example:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. Serverless (AWS Lambda / Google Cloud Functions)

The application can be adapted for serverless deployment using:
- AWS Lambda + API Gateway
- Google Cloud Functions
- Azure Functions

Note: May require adjustments for cold start times and memory limits.

## ⚠️ Limitations & Known Issues

1. **PDF Features**:
   - Encrypted PDFs require password handling (not yet implemented)
   - Digital signatures will be invalidated
   - Complex patterns/shadings may not transform correctly
   - Annotations and form fields may need separate handling

2. **Performance**:
   - Very large PDFs (100+ pages, 50+ MB) may take longer
   - Embedded high-resolution images slow processing

3. **Color Spaces**:
   - Spot colors (DeviceN, Separation) need additional handling
   - ICC color profiles are approximated to RGB

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Enhanced content stream parser for complex PDFs
- [ ] Support for encrypted PDFs
- [ ] Annotation and form field color transformation
- [ ] Batch processing multiple PDFs
- [ ] Progress updates via WebSocket
- [ ] Custom theme creation UI
- [ ] Undo/preview before download
- [ ] PDF metadata preservation options

## 📝 License

[Your License Here]

## 🙏 Acknowledgments

- Original project by [Chizkiyahu](https://github.com/Chizkiyahu/pdf-dark-mode-converter)
- PyMuPDF library for excellent PDF manipulation capabilities
- FastAPI for the modern Python web framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Made with ❤️ for better reading experiences**
