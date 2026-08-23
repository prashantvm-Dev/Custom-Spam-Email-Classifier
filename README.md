# 📧 Custom Spam Email Classifier

A web-based spam email classification system that connects to Gmail, retrieves emails, and automatically classifies them as **Spam** or **Safe** using Machine Learning.

## 🚀 Features

* 🔐 Google OAuth 2.0 authentication
* 📩 Gmail API integration
* 🤖 Machine Learning-based spam detection
* 🧹 Email text preprocessing
* 🔢 TF-IDF feature extraction
* 🧠 Multinomial Naive Bayes classifier
* 📊 Email classification statistics
* 🔎 Search emails
* 🏷️ Filter emails by Spam/Safe
* 📄 View complete email details
* 🔄 Refresh Gmail emails
* 📱 Responsive web interface

## 🛠️ Technologies Used

### Backend

* Python
* Flask
* Gmail API
* Google OAuth 2.0

### Machine Learning

* Pandas
* NumPy
* Scikit-learn
* TF-IDF
* Multinomial Naive Bayes

### Frontend

* HTML
* CSS
* JavaScript
* Chart.js

## 📂 Project Structure

```text
Custom-Spam-Email-Classifier/
│
├── app.py
├── requirements.txt
├── .gitignore
│
├── classifier/
│   ├── classifier.py
│   ├── preprocessing.py
│   └── feature_extraction.py
│
├── gmail/
│   └── gmail_api.py
│
├── dataset/
│   └── emails.csv
│
├── credentials/
│   └── credentials.json
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   └── email.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd Custom-Spam-Email-Classifier
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

### Windows

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 🔑 Google Gmail API Setup

1. Create a project in Google Cloud Console.
2. Enable the **Gmail API**.
3. Configure the OAuth consent screen.
4. Create OAuth 2.0 credentials.
5. Download the credentials file.
6. Place it inside:

```text
credentials/credentials.json
```

7. Make sure the redirect URI is configured as:

```text
http://127.0.0.1:5000/oauth2callback
```

## ▶️ Run the Project

Start the Flask application:

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

Click **Login with Google** and authorize Gmail access.

## 🔄 How It Works

```text
User
 ↓
Google Login
 ↓
OAuth Authentication
 ↓
Gmail API
 ↓
Fetch Emails
 ↓
Text Preprocessing
 ↓
TF-IDF Feature Extraction
 ↓
Multinomial Naive Bayes
 ↓
Spam / Safe Classification
 ↓
Dashboard
```

## 🤖 Machine Learning Workflow

The classifier follows these steps:

1. Load the email dataset.
2. Clean the email text.
3. Split the dataset into training and testing data.
4. Convert text into numerical features using TF-IDF.
5. Train a Multinomial Naive Bayes model.
6. Test the model using test data.
7. Use the trained model to classify Gmail emails.

## 📊 Dashboard

The dashboard displays:

* Total emails
* Spam emails
* Safe emails
* Spam percentage
* Classification chart
* Recent emails
* Search functionality
* Spam/Safe filters

## 🔐 Security

The following files should **not** be uploaded to GitHub:

```text
credentials/credentials.json
credentials/token.pickle
.env
```

They are excluded through `.gitignore`.

## 📌 Future Improvements

* Improve classification accuracy with a larger dataset.
* Add deep learning-based classification.
* Add automatic spam email labeling in Gmail.
* Add pagination for large inboxes.
* Add user-specific classification history.
* Add more detailed analytics.
* Deploy the application to a cloud platform.

## 👨‍💻 Project

**Custom Spam Email Classifier**

A Machine Learning and Web Development project combining:

**Python + Flask + Gmail API + Machine Learning + HTML/CSS/JavaScript**


# Custom Spam Email Classifier

## About the Project

The Custom Spam Email Classifier is a machine learning-based web application designed to automatically detect and classify emails as Spam or Safe (Ham).

The project uses Python, Flask, Scikit-learn, Pandas, TF-IDF, and Multinomial Naive Bayes. It also integrates with the Gmail API using OAuth 2.0 authentication.

## Features

- Spam and Safe email classification
- Machine learning-based detection
- Gmail API integration
- Google OAuth 2.0 authentication
- Email search and filtering
- Spam statistics dashboard
- Spam percentage visualization

## Technologies Used

- Python
- Flask
- HTML
- CSS
- JavaScript
- Pandas
- Scikit-learn
- Gmail API
- OAuth 2.0

## Machine Learning

The system uses TF-IDF for feature extraction and Multinomial Naive Bayes for email classification.

## Model Accuracy

The current model achieved approximately 95.8% accuracy on the test dataset.

## Security

Sensitive files such as `credentials.json`, `.env`, and OAuth tokens are not included in the repository.

## Future Improvements

- Advanced phishing detection
- Malicious link detection
- Multilingual email classification
- Improved machine learning models
- Email risk scoring
