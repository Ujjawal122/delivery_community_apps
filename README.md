# Delivery Community 🛵

A full-stack, location-aware community application built specifically for delivery partners. This app empowers delivery riders to share real-time route intelligence, report road hazards, review society gates, and participate in community discussions.

## 🌟 Key Features

*   **📍 Location Intelligence**
    *   **Hazard Reports:** Quickly report on-road issues like waterlogging, stray dogs, bad roads, and harassment spots using a fast, stylish interface.
    *   **Gate Intelligence:** View and submit specific intelligence about residential societies, including average waiting times, lift availability, parking rules, and guard strictness.
    *   **Live Tracking:** Background location tracking to notify you of nearby hazards while you ride.
*   **🗣️ Community Feed**
    *   Join sub-communities tailored to specific needs (Daily Discussions, Memes, Tips, News, Company Updates).
    *   Create posts with text and images.
    *   Engage with other riders through upvotes, comments, and bookmarks.
*   **🔐 Secure Authentication**
    *   Robust JWT-based authentication system.

## 🛠️ Tech Stack

**Frontend (Mobile App)**
*   **Framework:** React Native with Expo
*   **Styling:** NativeWind (Tailwind CSS for React Native)
*   **State Management:** Zustand
*   **Networking:** Axios
*   **Routing:** Expo Router (File-based routing)

**Backend (API)**
*   **Framework:** FastAPI (Python)
*   **Database:** PostgreSQL with PostGIS (for geospatial queries)
*   **ORM:** SQLAlchemy & GeoAlchemy2
*   **Caching:** Redis
*   **Image Storage:** Cloudinary
*   **Migrations:** Alembic

---

## 🚀 Getting Started

### Prerequisites
*   Node.js & npm (for frontend)
*   Python 3.10+ (for backend)
*   PostgreSQL with PostGIS extension installed
*   Redis server running
*   Cloudinary account (for image uploads)

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your environment variables in a `.env` file (Database URL, Redis URL, JWT Secret, Cloudinary keys).
5. Run database migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Expo development server:
   ```bash
   npx expo start
   ```
4. Press `a` to open in an Android Emulator, `i` for iOS Simulator, or scan the QR code with the Expo Go app on your physical device.

---

## 📂 Project Structure

```text
delivery_community/
├── backend/                  # FastAPI Application
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── core/             # Config, security, responses
│   │   ├── models/           # SQLAlchemy Database Models (User, Post, Gate, Hazard)
│   │   ├── routers/          # API Endpoints
│   │   ├── schemas/          # Pydantic validation schemas
│   │   └── services/         # Business logic & integrations
│   └── requirements.txt      # Python dependencies
│
└── frontend/                 # Expo React Native Application
    ├── app/                  # Screens and Navigation (Expo Router)
    ├── components/           # Reusable UI components
    ├── constants/            # Theming and constants
    ├── services/             # API calls and background tasks
    └── store/                # Zustand global state
```
