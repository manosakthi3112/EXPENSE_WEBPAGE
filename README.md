# Personal Finance Dashboard

A web-based personal finance application built with Flask and MongoDB. This tool allows users to register, log in, and track their daily, weekly, and monthly revenue and expenses through a clean, interactive dashboard with data visualizations.

## Table of Contents

- [Key Features](#key-features)
- [Live Demo](#live-demo)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Key Features

-   🔐 **User Authentication**: Secure user registration and login system with hashed passwords using `bcrypt`.
-   📊 **Interactive Dashboard**: A central dashboard (`/index`) to visualize financial health with:
    -   Daily revenue vs. expense bar chart.
    -   Weekly expense breakdown by category (pie chart).
    -   30-day revenue and expense trends (line chart).
-   📈 **Dynamic Statistics**: View financial summaries for the current day, last 7 days, and last 30 days.
-   🗂️ **Organized Data Entry**: A dedicated form (`/dashboard`) to easily submit revenue and expenses. Categories and items are linked dynamically.
-   🔒 **Data Isolation**: Each user's financial data is stored in a separate MongoDB collection for privacy and security.
-   📜 **Transaction History**: View complete tables of all recorded revenue and expense transactions.
-   ⚙️ **Environment-Based Configuration**: Securely manage database credentials and secret keys using a `.env` file.
-   ✅ **Form Validation**: Server-side validation to ensure data integrity (e.g., amounts must be positive).

## Live Demo

*(Optional: Add a link to a live, deployed version of your application if you have one.)*

`[Link to your live demo]`

## Technology Stack

-   **Backend**: Flask (Python Web Framework)
-   **Database**: MongoDB (NoSQL Database) with `pymongo` driver
-   **Frontend**: HTML, CSS, JavaScript (with Jinja2 for templating)
-   **Authentication**: `bcrypt` for password hashing
-   **Environment Management**: `python-dotenv`
-   **Deployment**: Can be deployed on platforms like Heroku, Vercel, or any VPS.

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

-   **Python 3.8+** and **Pip**
-   **A MongoDB instance**:
    -   You can use a local MongoDB server.
    -   Or, for an easy start, create a free cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register). **Remember to whitelist your IP address** in the Atlas security settings.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create and activate a virtual environment:**
    -   **On macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    -   **On Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required packages:**
    Create a `requirements.txt` file with the following content:
    ```txt
    Flask
    pymongo
    bcrypt
    python-dotenv
    certifi
    ```
    Then, install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a file named `.env` in the root directory of the project. Copy the contents of the example below and replace the placeholder values with your actual credentials.

    ```env
    # MongoDB Connection URI - Replace with your own from MongoDB Atlas or local instance
    MONGO="mongodb+srv://<username>:<password>@<cluster-url>/<database-name>?retryWrites=true&w=majority"
    ```
    *   **MONGO**: Your full MongoDB connection string.
    *   The `app.py` file uses `"123355"` as a `SECRET_KEY`. For production, it's highly recommended to move this to the `.env` file as well for better security.

## Running the Application

Once the setup is complete, you can start the Flask development server:

```bash
python app.py

##Project Structure

.
├── .env                  # Environment variables (you must create this)
├── app.py                # Main Flask application file
├── requirements.txt      # Python dependencies
├── static/               # For CSS, JS, and image files (if you add them)
│   └── css/
│       └── style.css
└── templates/            # HTML templates
    ├── home.html         # The main dashboard with charts and stats
    ├── index.html        # The data entry form
    ├── login.html        # User login page
    └── register.html     # User registration page
