# CortexCart - Multi-Modal Product Recommendation System

<p align="center">
  <strong>An AI-powered e-commerce recommendation engine built with Flask, React, and scikit-learn</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.1-green?logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikit-learn&logoColor=white" />
</p>

---

## Overview

**CortexCart** is a full-stack multi-modal product recommendation system that uses machine learning to find similar products from a catalog of **93,000+ luxury products** sourced from JomaShop. It combines **TF-IDF text analysis**, **price normalization**, and **brand encoding** into a hybrid content-based recommendation engine, served through a Flask REST API and consumed by a premium React frontend with glassmorphism UI design.

The system supports three recommendation modes:
1. **Product-based** — Select any product to find visually and contextually similar items
2. **Query-based** — Type a natural language search with optional brand filtering
3. **Batch processing** — Upload a CSV of queries and get bulk recommendations

---

## Features

### Backend
- **Hybrid ML Pipeline** — Combines TF-IDF text features (20,000 dimensions, bigrams, sublinear TF), MinMaxScaler price normalization, and LabelEncoder brand one-hot encoding
- **Weighted Feature Fusion** — Text (1.0), Price (0.3), Brand (0.5) weights for balanced recommendations
- **Cosine Similarity Search** — Fast similarity computation across 93,000+ products
- **Model Caching** — Trained models are serialized with joblib for fast restarts
- **RESTful API** — Clean Flask endpoints with pagination, search, and error handling
- **Batch Processing** — Upload CSV files for bulk recommendation generation
- **Production Ready** — Gunicorn server with configurable workers and timeout

### Frontend
- **Premium Dark Theme** — Glassmorphism design with frosted glass effects and gradient accents
- **Animated UI** — Smooth page transitions and card animations with Framer Motion
- **Responsive Design** — Fully responsive grid layouts that adapt to any screen size
- **Real-time Search** — Instant product catalog search with debouncing
- **Paginated Catalog** — Browse 93,000+ products with smooth page navigation
- **Drag & Drop** — CSV file upload with drag-and-drop support for batch mode
- **Similarity Scores** — Visual display of match percentages on recommended products
- **Discount Badges** — Automatic calculation and display of discount percentages

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    React Frontend                    │
│         (Vite + React 18 + Framer Motion)           │
│                                                     │
│  ┌───────────┐ ┌───────────┐ ┌──────────────────┐  │
│  │ HomePage   │ │ Catalog   │ │ Recommendations  │  │
│  │           │ │ Page      │ │ Page             │  │
│  └───────────┘ └───────────┘ └──────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │              BatchPage (CSV Upload)            │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (axios)
                       ▼
┌─────────────────────────────────────────────────────┐
│                   Flask REST API                     │
│                                                     │
│  /api/health          GET    Health check           │
│  /api/products        GET    Paginated catalog      │
│  /api/products/:id    GET    Single product         │
│  /api/recommend/      POST   Real-time recs         │
│    realtime                                         │
│  /api/recommend/      POST   Batch CSV recs         │
│    batch                                            │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│            Recommendation Engine (ML)                │
│                                                     │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────┐  │
│  │ TF-IDF      │  │ Price      │  │ Brand       │  │
│  │ Vectorizer  │  │ Scaler     │  │ Encoder     │  │
│  │ (20K feat)  │  │ (MinMax)   │  │ (Top 200)   │  │
│  └──────┬──────┘  └─────┬──────┘  └──────┬──────┘  │
│         │    weight=1.0  │  weight=0.3    │ w=0.5   │
│         └───────────┬────┴────────────────┘         │
│                     ▼                               │
│          Sparse Feature Matrix (hstack)             │
│                     │                               │
│                     ▼                               │
│           Cosine Similarity Search                  │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              JomaShop Dataset (CSV)                  │
│           93,931 products · 1,436 brands             │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 | UI component library |
| **Build Tool** | Vite 6 | Fast dev server & production bundler |
| **Routing** | React Router DOM 6 | Client-side SPA routing |
| **Animation** | Framer Motion 11 | Page transitions & micro-interactions |
| **Icons** | Lucide React | SVG icon library |
| **HTTP Client** | Axios | API communication |
| **Backend** | Flask 3.1 | REST API framework |
| **CORS** | Flask-CORS | Cross-origin request handling |
| **ML - Text** | TfidfVectorizer (scikit-learn) | Text feature extraction |
| **ML - Numeric** | MinMaxScaler (scikit-learn) | Price normalization |
| **ML - Categorical** | LabelEncoder (scikit-learn) | Brand encoding |
| **ML - Similarity** | cosine_similarity (scikit-learn) | Product matching |
| **Data** | Pandas, NumPy | Data processing & manipulation |
| **Serialization** | Joblib | Model persistence |
| **Sparse Matrix** | SciPy | Efficient feature storage |
| **Production Server** | Gunicorn | WSGI HTTP server |

---

## Dataset

The project uses the **JomaShop Products Dataset** containing **93,931 luxury products** across watches, jewelry, accessories, and more.

| Column | Description |
|--------|-------------|
| `product_type` | SimpleProduct, ConfigurableProduct, GroupedProduct |
| `name` | Product name |
| `brandName` | Brand (1,436 unique brands) |
| `stockStatus` | In stock / Out of stock |
| `description.short` | Brief product description |
| `description.complete` | Full product description |
| `genderLabel` | Target gender |
| `department` | Product department/category |
| `pricing.regularPrice.value` | Regular price |
| `pricing.finalPrice.value` | Sale/final price |
| `pricing.retailPrice.value` | Retail (MSRP) price |

---

## Recommendation Engine

The engine (`backend/recommendation_engine.py`) implements a **hybrid content-based filtering** approach that fuses three modalities:

### 1. Text Features (Weight: 1.0)
- Combines `name`, `description.short`, and `description.complete` into a single text blob
- Applies **TF-IDF Vectorization** with:
  - 20,000 max features
  - Unigrams and bigrams (`ngram_range=(1,2)`)
  - Sublinear TF scaling (`sublinear_tf=True`)
  - English stop word removal

### 2. Price Features (Weight: 0.3)
- Normalizes `finalPrice` and computed `discount_pct` using **MinMaxScaler**
- Discount percentage is derived as: `(retailPrice - finalPrice) / retailPrice × 100`
- Ensures price-similar products rank higher

### 3. Brand Features (Weight: 0.5)
- Encodes the **top 200 brands** using one-hot encoding
- Remaining brands are grouped as "Other"
- Provides brand affinity in recommendations

### Similarity Computation
All features are combined into a single sparse matrix using `scipy.sparse.hstack`, with each modality weighted according to its importance. **Cosine similarity** is then computed between the query vector and all products to rank results.

### Brand Boost
For query-based recommendations, an additional **0.15 score boost** is applied to products matching the requested brand, ensuring brand-relevant results surface higher.

---

## API Endpoints

### `GET /api/health`
Health check endpoint.
```json
{ "status": "ok" }
```

### `GET /api/products?page=1&per_page=20&search=omega`
Paginated product catalog with optional search.
```json
{
  "products": [...],
  "total": 93931,
  "page": 1,
  "per_page": 20,
  "total_pages": 4697
}
```

### `GET /api/products/:id`
Single product by index.
```json
{
  "id": 42,
  "name": "Omega Speedmaster Professional",
  "brandName": "Omega",
  "finalPrice": 5350,
  "retailPrice": 7150,
  "discount_pct": 25.2,
  ...
}
```

### `POST /api/recommend/realtime`
Get recommendations by product ID or text query.

**By product ID:**
```json
{
  "product_id": 42,
  "top_n": 10
}
```

**By query + brand:**
```json
{
  "query": "luxury diving watch",
  "brand": "Omega",
  "top_n": 10
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "id": 156,
      "name": "Omega Seamaster Planet Ocean",
      "similarity_score": 0.8743,
      ...
    }
  ]
}
```

### `POST /api/recommend/batch`
Upload a CSV with `query` and optional `brand` columns. Returns JSON or downloadable CSV.

```
Content-Type: multipart/form-data
file: queries.csv
top_n: 5
format: json|csv
```

---

## Project Structure

```
CortexCart/
├── .gitignore
├── build.sh                          # Render build script
├── render.yaml                       # Render deployment blueprint
├── main.py                           # Original ML exploration script
├── sample_batch_queries.csv          # Sample CSV for batch testing
│
├── backend/
│   ├── app.py                        # Flask API server
│   ├── recommendation_engine.py      # ML recommendation engine
│   └── requirements.txt              # Python dependencies
│
├── frontend/
│   ├── index.html                    # HTML entry point
│   ├── package.json                  # Node.js dependencies
│   ├── vite.config.js                # Vite configuration (proxy, port)
│   └── src/
│       ├── main.jsx                  # React entry + BrowserRouter
│       ├── App.jsx                   # Route definitions
│       ├── styles/
│       │   └── global.css            # Global dark theme + CSS variables
│       ├── services/
│       │   └── api.js                # Axios API service layer
│       ├── components/
│       │   ├── Navbar.jsx            # Navigation bar (glassmorphism)
│       │   ├── Navbar.css
│       │   ├── ProductCard.jsx       # Animated product card
│       │   ├── ProductCard.css
│       │   ├── Loader.jsx            # Loading spinner animation
│       │   └── Loader.css
│       └── pages/
│           ├── HomePage.jsx          # Landing page (hero + stats)
│           ├── HomePage.css
│           ├── CatalogPage.jsx       # Product grid + search + pagination
│           ├── CatalogPage.css
│           ├── BatchPage.jsx         # CSV drag-and-drop upload
│           ├── BatchPage.css
│           ├── RecommendationsPage.jsx  # Similar products display
│           └── RecommendationsPage.css
│
├── Dataset/
│   ├── JomaShop Products Data.csv    # Main dataset (93,931 products)
│   └── testdata.csv                  # Test dataset
│
├── models/                           # Pre-trained ML model artifacts
│   ├── Untitled.ipynb                # Jupyter notebook (EDA + classification)
│   └── *.pkl                         # Serialized model files
│
└── BG_image/
    └── background.png                # Background image asset
```

---

## Getting Started

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **npm** or **yarn**

### 1. Clone the Repository
```bash
git clone https://github.com/Premkumar1845/CortexCart.git
cd CortexCart
```

### 2. Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Start the Flask Server
```bash
cd backend
python app.py
```
The engine will take about a minute to build the TF-IDF model on first run. Subsequent starts are faster due to model caching.

> Server runs at `http://localhost:5000`

### 4. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 5. Start the React Dev Server
```bash
npm run dev
```
> Frontend runs at `http://localhost:3000` with API proxy to Flask

### 6. Open the App
Navigate to **http://localhost:3000** in your browser.

---

## Sample Batch CSV

A sample file (`sample_batch_queries.csv`) is included for testing batch recommendations:

```csv
query,brand
omega speedmaster,Omega
rolex submariner,Rolex
diamond necklace,
gucci handbag,Gucci
seiko automatic watch,Seiko
ray ban sunglasses,Ray-Ban
mont blanc pen,Montblanc
casio g-shock,Casio
tissot dress watch,Tissot
gold bracelet,
```

Upload this file on the **Batch Upload** page to test bulk recommendation generation.



This project is for educational and portfolio purposes.

---

