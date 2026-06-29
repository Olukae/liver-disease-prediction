# LiverPredict AI
### Intelligent ICT-Based Liver Disease Prediction System

A production-ready, AI-powered web application for liver disease risk prediction built with Python Flask and scikit-learn. Enter nine liver function test parameters and receive an instant risk level, confidence score, contributing factors, personalized recommendations, and a downloadable PDF report.

---

## Features

| Module | Description |
|---|---|
| **Authentication** | Register, login, logout, password reset, profile management |
| **Multi-step Form** | Guided, validated 4-step prediction form with voice input |
| **ML Prediction** | Gradient Boosting classifier trained on the ILPD UCI dataset (583 records) |
| **Risk Analysis** | Low / Medium / High risk with confidence gauge |
| **Factor Breakdown** | Identifies abnormal biomarkers with clinical reference ranges |
| **Recommendations** | Personalized, risk-adjusted health guidance |
| **PDF Reports** | Clinic-ready PDF with patient details, results, factors, recommendations |
| **Prediction History** | Search, filter by date and risk, download per-record PDFs |
| **AI Chat Widget** | Built-in health assistant explaining markers and results |
| **Admin Dashboard** | User management, prediction monitoring, analytics, CSV export |
| **Interactive Charts** | Risk distribution, prediction trends, user activity, parameter analysis |
| **Dark Mode** | Full dark theme toggle, preference persisted across sessions |
| **Voice Input** | Web Speech API integration for hands-free form and chat input |

---

## Quick Start

### Prerequisites
- Python 3.9+

### Linux / macOS
```bash
git clone <repo>
cd liverpredict
chmod +x run.sh
./run.sh
```

With demo data:
```bash
SEED=1 ./run.sh
```

### Windows
```cmd
run.bat
```

Then open **http://localhost:5000** in your browser.

---

## Default Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@liverpredict.ai | Admin@12345 |
| Patient (demo) | adeola@example.com | Demo@12345 |

> **Change admin credentials before deploying to production.**

---

## Project Structure

```
liverpredict/
├── app.py                   # Application entry point
├── config.py                # Configuration (SQLite / MySQL, mail, paths)
├── seed.py                  # Demo data seeder
├── run.sh / run.bat         # Quick-start scripts
├── requirements.txt
├── .env.example             # Environment variable template
│
├── app/
│   ├── __init__.py          # App factory
│   ├── extensions.py        # Flask extensions (db, login, bcrypt, mail)
│   ├── models.py            # User & PredictionRecord models
│   ├── forms.py             # WTForms definitions
│   ├── routes/
│   │   ├── auth.py          # Register, login, logout, reset, profile
│   │   ├── main.py          # Landing page, dashboard, health tips
│   │   ├── prediction.py    # New prediction, result, history, PDF download
│   │   ├── admin.py         # Admin dashboard, user mgmt, exports
│   │   └── api.py           # JSON API (charts, AI chat)
│   ├── templates/           # Jinja2 HTML templates
│   └── static/
│       ├── css/style.css    # Full design system (glassmorphism, dark mode)
│       ├── js/main.js       # Toast, dark mode, sidebar, chat, voice
│       ├── js/charts.js     # Chart.js rendering for analytics
│       └── js/steps.js      # Multi-step form controller
│
├── ml/
│   ├── train_model.py       # Model training script
│   ├── predictor.py         # Prediction service (loads model, generates analysis)
│   ├── ilpd_dataset.csv     # Indian Liver Patient Dataset (UCI)
│   ├── liver_model.joblib   # Trained model (auto-generated)
│   └── model_meta.json      # Feature order, importances, normal ranges
│
├── utils/
│   └── pdf_report.py        # ReportLab PDF generation
│
└── instance/
    ├── liverpredict.db      # SQLite database (auto-created)
    └── reports/             # Generated PDF reports
```

---

## Configuration

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

### Using MySQL instead of SQLite

```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/liver_predict
```

Create the database first:
```sql
CREATE DATABASE liver_predict CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Email (Password Reset)

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_SUPPRESS_SEND=0
```

---

## ML Model

- **Dataset**: Indian Liver Patient Dataset (ILPD), UCI Machine Learning Repository
- **Records**: 583 (416 disease, 167 no disease)
- **Best model**: Gradient Boosting Classifier (cross-val F1 ≈ 0.81)
- **Features**: Age, Gender, Total Bilirubin, Direct Bilirubin, Alkaline Phosphatase, ALT, AST, Total Protein, Albumin, A/G Ratio

To retrain the model:
```bash
python ml/train_model.py
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask, Flask-Login, Flask-WTF, Flask-Bcrypt, Flask-SQLAlchemy, Flask-Mail |
| **ML** | scikit-learn (Gradient Boosting), pandas, numpy, joblib |
| **Database** | SQLite (default) / MySQL via PyMySQL |
| **PDF** | ReportLab |
| **Frontend** | HTML5, CSS3, Bootstrap 5, Chart.js, Font Awesome 6 |
| **Fonts** | Sora (display), Manrope (body) |

---

## API Endpoints

| Route | Auth | Description |
|---|---|---|
| `GET /api/charts/risk-distribution` | Admin | Risk level pie chart data |
| `GET /api/charts/predictions-trend` | Admin | 14-day predictions trend |
| `GET /api/charts/user-activity` | Admin | 14-day registration trend |
| `GET /api/charts/parameter-analysis` | Admin | Disease vs healthy avg parameters |
| `GET /api/charts/my-history` | Patient | Personal confidence trend |
| `POST /api/chat` | Any | AI health assistant |

---

## Disclaimer

LiverPredict AI is a clinical decision-support tool built on a real dataset and ML model. Results are for informational purposes only and must not be used as a substitute for professional medical diagnosis. Always consult a licensed physician.

---

*Built for the Intelligent ICT-Based Liver Disease Prediction System project.*
