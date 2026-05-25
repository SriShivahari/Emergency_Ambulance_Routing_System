# AI-Based Real-Time Ambulance Routing System

---

## Features

- Real-time ambulance route optimization
- Machine Learning-based traffic prediction
- Smart routing engine for emergency navigation
- Flask-based backend API
- Interactive dashboard visualization
- Route comparison and performance analytics
- Support for Chennai hospital datasets
- Traffic-aware decision making

---

## Tech Stack

### Backend
- Python
- Flask
- Flask-CORS

### Machine Learning
- Scikit-learn
- XGBoost
- NumPy
- Pandas
- Joblib

### Visualization
- Matplotlib
- Seaborn

### Other Tools
- Requests
- Polyline
- Python-dotenv

---

## Project Structure

```bash
Ambulance-Routing/
│
├── app/
│   ├── ml/                    # ML training, datasets, models
│   ├── routes/                # Flask API routes
│   ├── services/              # Routing and prediction services
│   ├── static/                # CSS, JS, datasets, graphs
│   └── templates/             # HTML templates
│
├── requirements.txt           # Python dependencies
├── run.py                     # Application entry point
├── .env                       # Environment variables
├── .gitignore
└── README.md