# 🩺 AI-Driven Public Health Chatbot for Disease Awareness

An AI and NLP-powered public health chatbot that provides disease awareness, symptom guidance, preventive healthcare information, and personalized conversational support through an interactive web application.

---

## 📖 Overview

The **AI-Driven Public Health Chatbot for Disease Awareness** is a web-based intelligent healthcare assistant developed using **Artificial Intelligence (AI)** and **Natural Language Processing (NLP)**. The chatbot enables users to interact using natural language and receive reliable information about diseases, symptoms, preventive measures, healthy lifestyle practices, and general public health awareness.

The application is designed to improve health literacy by making evidence-based healthcare information easily accessible. It uses conversational AI to understand user queries and generate meaningful, context-aware responses while encouraging users to seek professional medical advice for diagnosis and treatment.

---

## 🛠️ Tech Stack

### Backend

* Python
* Flask
* SQLite
* Groq API
* Python Dotenv
* Werkzeug

### Frontend

* HTML5
* CSS3
* JavaScript

### AI & NLP

* Artificial Intelligence (AI)
* Natural Language Processing (NLP)
* Large Language Model (LLM) Integration

---

## 📂 Project Structure

```text
AI-Public-Health-Chatbot/
│
├── app.py                  # Main Flask application
├── healthbot.db            # SQLite database
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
├── decision.py             # ML-related script
│
├── templates/
│   ├── landing.html
│   ├── auth.html
│   ├── chat.html
│   └── index.html
│
└── README.md
```

---

## ⚙️ How It Works

1. User registers or logs into the application.
2. The user enters a health-related question.
3. The chatbot processes the query using NLP techniques.
4. AI understands the user's intent and context.
5. The system generates an informative response using the Groq LLM.
6. Conversations are securely stored in a SQLite database for future reference.

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-public-health-chatbot.git
cd ai-public-health-chatbot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file and add:

```env
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key
```

### 5. Run the Application

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
```

---

## 💡 NLP Capabilities

The chatbot leverages Natural Language Processing to:

* Understand natural language queries
* Recognize user intent
* Interpret health-related questions
* Generate context-aware responses
* Improve conversational interactions
* Deliver easy-to-understand health information

---

## 🩺 Healthcare Topics Covered

* Diabetes
* Hypertension
* Dengue
* Malaria
* COVID-19
* Influenza
* Asthma
* Tuberculosis
* Healthy Lifestyle
* Nutrition
* Hygiene
* Vaccination
* Mental Health Awareness

---

## ✨ Features

* 🤖 AI-powered conversational health assistant
* 🧠 Natural Language Processing (NLP) for understanding user queries
* 🩺 Disease awareness and public health education
* 💬 Symptom-based general guidance
* 🛡️ Preventive healthcare recommendations
* 🥗 Healthy lifestyle and wellness tips
* 🔐 Secure user authentication (Login & Registration)
* 💾 Persistent chat history using SQLite
* 📱 Responsive and user-friendly interface
* ⚡ Fast AI responses powered by the Groq API

---

## 🎯 Objectives

* Improve public health awareness.
* Promote disease prevention.
* Provide reliable healthcare information.
* Encourage healthy lifestyle habits.
* Demonstrate AI and NLP applications in healthcare.
* Enhance accessibility to health education.

---

## 📈 Future Enhancements

* Voice-enabled chatbot
* Multilingual support
* Healthcare API integration
* Personalized health recommendations
* Appointment booking
* Medical image analysis
* Mobile application
* Advanced AI models
* Analytics dashboard for user insights

