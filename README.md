# 🌾 AI-Driven Crop Recommendation System

A Django-based web application that provides AI-powered, personalized crop recommendations to farmers based on soil properties, weather forecasts, and crop rotation history.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

- **🧪 Soil Analysis** — Integration with Soil Grids API (ISRIC) for global soil data, with ICAR-based regional estimates as fallback for Indian locations
- **🌤️ Weather Integration** — Real-time weather data and 7-day forecasts via Open-Meteo (free, no API key needed) with optional OpenWeatherMap support
- **🌱 Crop Recommendations** — ML-powered suggestions with yield, profit, and sustainability predictions
- **🏡 Farm & Field Management** — Register multiple farms/fields with GPS coordinates, soil data, and crop history
- **🌐 Multilingual Support** — Interface available in English, Hindi, Telugu, Tamil, Kannada, and Marathi
- **💬 Chat Interface** — Text-based chat for farming queries
- **📊 Dashboard** — Overview of farms, fields, soil data, weather, and recommendations

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Django 4.2, Django REST Framework |
| **Database** | SQLite (dev), PostgreSQL (production) |
| **ML/AI** | scikit-learn, TensorFlow |
| **Weather API** | Open-Meteo (free, default) / OpenWeatherMap (optional) |
| **Soil API** | ISRIC Soil Grids v2.0 + Indian regional estimates (ICAR) |
| **Frontend** | Django Templates, Bootstrap 5, JavaScript |
| **Task Queue** | Celery + Redis (optional) |

---

## 📁 Project Structure

```
CropRecommendation/
├── apps/
│   ├── users/              # User authentication & profiles
│   ├── farms/              # Farm & field management
│   ├── soil/               # Soil data (Soil Grids API + regional estimates)
│   ├── weather/            # Weather data (Open-Meteo / OpenWeatherMap)
│   ├── recommendations/    # ML-based crop recommendation engine
│   ├── chat/               # Chat interface
│   └── translation/        # Multilingual translation services
├── crop_recommendation/    # Django project settings & URLs
├── static/                 # CSS, JavaScript
├── templates/              # Base HTML templates
├── ml_training/            # ML model training scripts & data
├── logs/                   # Application logs
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Setup

### Prerequisites

- **Python 3.10+** — [Download here](https://www.python.org/downloads/)
- **pip** (comes with Python)
- **Git** (for cloning)

> 📖 For detailed step-by-step instructions, see **[QUICK_START.md](QUICK_START.md)**

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/CropRecommendation.git
cd CropRecommendation
```

### 2. Create & Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Setup Database & Run

```bash
python manage.py migrate
python manage.py createsuperuser   # Create admin account
python manage.py collectstatic     # Collect static files
python manage.py runserver         # Start dev server
```

### 5. Open in Browser

| Page | URL |
|------|-----|
| Home | http://127.0.0.1:8000/ |
| Dashboard | http://127.0.0.1:8000/dashboard/ |
| Admin Panel | http://127.0.0.1:8000/admin/ |

---

## 🔌 API Configuration

### Weather Data (Works out of the box ✅)

The app uses **Open-Meteo** by default — a free weather API that requires **no API key**. It provides:
- Current weather (temperature, humidity, wind, rain, pressure)
- Up to 16-day forecast
- Global coverage

**Optional:** If you have an OpenWeatherMap API key, set it for enhanced data:
```env
OPENWEATHER_API_KEY=your-key-here
```

### Soil Data (Works out of the box ✅)

The app uses two data sources:
1. **ISRIC Soil Grids v2.0** — Global soil data (pH, nitrogen, organic carbon, clay/sand content)
2. **Indian Regional Estimates** — ICAR-based fallback for 15+ Indian agro-climatic zones

No API key needed for either source.

> **Note:** Soil Grids may not have data for urban areas. The app automatically falls back to regional estimates for Indian locations.

---

## 🌍 Environment Variables (Optional)

Create a `.env` file in the project root for production or advanced configuration:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Weather (optional — Open-Meteo is used as free default)
OPENWEATHER_API_KEY=your-openweathermap-key

# Translation (optional)
GOOGLE_TRANSLATE_API_KEY=your-google-translate-key
LIBRETRANSLATE_URL=https://libretranslate.com
```

---

## 📱 App Workflow

```
Register/Login → Add Farm (with GPS coordinates)
                    ↓
              Add Field (within farm)
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
   Fetch Soil   Fetch Weather   Add Crop
   Data (API)   Data (API)      History
        ↓           ↓           ↓
        └───────────┼───────────┘
                    ↓
          Get Crop Recommendations
                    ↓
          View Predictions & Insights
```

---

## 🧪 Running Tests

```bash
python manage.py test
python manage.py check    # Check for configuration issues
```

---

## 🔧 Development Commands

| Command | Description |
|---------|-------------|
| `python manage.py runserver` | Start dev server |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Create new migrations |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py collectstatic` | Collect static files |
| `python manage.py test` | Run tests |
| `python manage.py shell` | Open Django shell |

---

## 📋 Troubleshooting

| Issue | Solution |
|-------|----------|
| `python` not found | Use `python3` (Mac) or `py` (Windows). Ensure Python is in PATH. |
| PowerShell execution policy error | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Port 8000 in use | Use: `python manage.py runserver 8001` |
| Static files not loading | Run: `python manage.py collectstatic --noinput` |
| Database errors | Delete `db.sqlite3` and run `python manage.py migrate` again |
| `ModuleNotFoundError` | Ensure venv is activated (`(venv)` in prompt), then `pip install -r requirements.txt` |

---

## 👥 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📧 Contact

**Email:** kathulavikasr@gmail.com

---

## 📄 License

This project is developed for educational and research purposes.
