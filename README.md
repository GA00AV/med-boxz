# 🩺 **MedBoxz – AI-Powered Medical Consultation Assistant**

**AI-driven consultation booking & patient-doctor interaction system built using LangGraph, LangChain, MongoDB, Redis & Streamlit.**

MedBoxz is an intelligent medical consultation platform that allows users to **book appointments, manage consultations, retrieve payment links, request refunds, access consultation history**, and more — all through a conversational AI agent.

This project demonstrates a **full AI workflow orchestration** using LangGraph + LLMs + real backend tools.

---

## 🚀 **Features**

### ⭐ AI-Powered Consultation Assistant

Built using **LangGraph** and **Google Gemini**, the AI assistant can:

* Book appointments (doctor selection, time slots, payment link creation)
* Access verified patient history
* Cancel consultations & initiate refunds
* Retrieve payment links
* Apply for manual reviews

---

### ⭐ Fully Functional Backend

The backend includes real-world integrations:

* **MongoDB** → Store users, doctors, consultations, manual reviews
* **Redis** → Handle time slot reservations + token tracking
* **Tavily Search** → Web search for identifying doctor speciality from symptoms
* **LangGraph State Machine** → Multi-step conversational workflow
* **Custom Tools** for all operations (booking, cancellation, fetching data, etc.)

---

### ⭐ Streamlit Frontend

A clean chat interface where users interact with the AI assistant in real time.

---

## 🏗️ **Tech Stack**

### **Backend**

* 🧠 LangChain + LangGraph
* 🤖 Google Gemini 2.5 Flash
* 🍃 MongoDB
* ⚡ Redis
* 🌍 Tavily Search API
* 🔧 Python (Backend Toolkit)

### **Frontend**

* 🎨 Streamlit
* 💬 Streamlit Chat UI

---



## 💻 **Running Locally**

### 1️⃣ Install Dependencies

```sh
pip install -r requirements.txt
```

### 2️⃣ Set Up Environment Variables

Create `.env` file:

```
GOOGLE_API_KEY=...
TAVILY_API_KEY=...
DB_NAME="medboxz"
USER_COLLECTION="users"
MANUAL_REVIEWS_COLLECTION="manual_reviews"
CONSULTATIONS_COLLECTION="consultations"
MONGO_URI="mongodb://localhost:27017"
REDIS_URL="redis://localhost:6379/0"
```

### 3️⃣ Apply migrations to MongoDB (ONLY FOR FIRST TIME)

````commandline
python migrations.py
````

### 4️⃣ Start Streamlit UI

```sh
streamlit run src/main.py
```
### 4️⃣ Run API_handler for payments

```sh
python "src/API handler.py"
```
---

## 🎥 **Demo**

http://demo.com
