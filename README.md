# 🏥 MedReport AI — AI-Powered Medical Report Summarizer

> An intelligent web application that uses **Azure AI Services** to analyze medical reports, extract key findings, identify abnormal values, and provide actionable summaries.

## 📋 Table of Contents
- [About](#about)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Azure Services Used](#azure-services-used)
- [Setup & Installation](#setup--installation)
- [Running the App](#running-the-app)
- [Project Structure](#project-structure)
- [Screenshots](#screenshots)
- [Future Enhancements](#future-enhancements)
- [Author](#author)

---

## 📖 About

**MedReport AI** is a web application built as part of my **Summer Training 2026** project after completing the **Microsoft Certified: Azure AI Fundamentals (AI-900)** certification.

The application demonstrates practical usage of Azure AI services by solving a real-world healthcare problem: **making medical reports easier to understand** for patients and healthcare professionals.

### Problem Statement
Medical reports are often complex, filled with technical jargon, and difficult for patients to interpret. This leads to:
- Anxiety due to lack of understanding
- Missed follow-up on abnormal values
- Delayed medical attention

### Solution
MedReport AI provides an instant, AI-powered analysis of medical reports that:
- Extracts text from uploaded PDFs and images
- Identifies and highlights abnormal values
- Provides a severity assessment
- Suggests actionable recommendations

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Document Extraction** | Extracts text, tables, and key-value pairs from PDFs and images using Azure Document Intelligence |
| 🤖 **AI Summarization** | GPT-4o analyzes the report and generates a structured summary |
| ⚠️ **Abnormal Value Detection** | Automatically identifies out-of-range lab values with explanations |
| 📊 **Severity Assessment** | Color-coded severity rating (Normal → Critical) |
| 💡 **Recommendations** | AI-generated follow-up suggestions based on findings |
| 📋 **Report History** | View and manage all previously analyzed reports |
| ☁️ **Cloud Storage** | Reports stored securely in Azure Blob Storage |
| 📱 **Responsive Design** | Works on desktop, tablet, and mobile browsers |

---

## 🏗️ Architecture

```
User Upload → Flask Web App → Azure Document Intelligence (OCR/Text Extraction)
                                        ↓
                              Azure Blob Storage (File Storage)
                                        ↓
                              Azure OpenAI GPT-4o (Analysis & Summary)
                                        ↓
                              Results Dashboard (Web UI)
```

### Data Flow
1. User uploads a medical report (PDF/image) via the web interface
2. File is stored in Azure Blob Storage for persistence
3. Azure Document Intelligence extracts text, tables, and structured data
4. Extracted content is sent to Azure OpenAI (GPT-4o) for analysis
5. AI returns structured summary with key findings, abnormal values, and recommendations
6. Results are saved to SQLite database and displayed on the dashboard

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Backend** | Python 3.10+, Flask |
| **Database** | SQLite (via Flask-SQLAlchemy) |
| **AI Services** | Azure Document Intelligence, Azure OpenAI (GPT-4o) |
| **Cloud Storage** | Azure Blob Storage |
| **Deployment** | Azure App Service (optional) |

---

## ☁️ Azure Services Used

### 1. Azure AI Document Intelligence
- **Purpose**: Extract text, tables, and key-value pairs from medical report PDFs and images
- **Model**: `prebuilt-layout` — optimized for structured document extraction
- **AI-900 Topic**: Computer Vision, Optical Character Recognition

### 2. Azure OpenAI Service
- **Purpose**: Analyze extracted text and generate structured medical summaries
- **Model**: GPT-4o — latest multimodal model for accurate medical analysis
- **AI-900 Topic**: Natural Language Processing, Generative AI

### 3. Azure Blob Storage
- **Purpose**: Securely store uploaded medical report files
- **AI-900 Topic**: Cloud Computing Fundamentals

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10 or higher
- An Azure account with active subscription (Azure for Students works!)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/medical-report-summarizer.git
cd medical-report-summarizer
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Azure Setup
Follow the detailed guide in [setup_azure.md](setup_azure.md) to create the required Azure resources.

### Step 4: Configure Environment
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env and fill in your Azure credentials
notepad .env
```

### Step 5: Run the Application
```bash
python run.py
```

Open your browser and navigate to: **http://127.0.0.1:5000**

---

## 📁 Project Structure

```
medical-report-summarizer/
├── app/
│   ├── __init__.py                   # Flask app factory
│   ├── config.py                     # Azure credentials configuration
│   ├── models.py                     # SQLite database models
│   ├── routes.py                     # Web routes and request handlers
│   ├── services/
│   │   ├── document_intelligence.py  # Azure Document Intelligence client
│   │   ├── openai_summarizer.py      # Azure OpenAI summarization
│   │   ├── blob_storage.py           # Azure Blob Storage management
│   │   └── report_analyzer.py        # Pipeline orchestrator
│   ├── templates/
│   │   ├── base.html                 # Base layout template
│   │   ├── index.html                # Upload page
│   │   ├── result.html               # Results dashboard
│   │   ├── history.html              # Report history
│   │   └── loading.html              # Processing animation
│   └── static/
│       ├── css/style.css             # Custom styling
│       └── js/app.js                 # Client-side interactivity
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── run.py                            # Application entry point
├── setup_azure.md                    # Azure setup guide
└── README.md                         # This file
```

---

## 🔮 Future Enhancements

- [ ] PDF download of analysis summary
- [ ] Voice-based report reading using Azure Speech Service
- [ ] Multi-language support using Azure Translator
- [ ] Report comparison (track health changes over time)
- [ ] Email notifications for critical findings
- [ ] Deploy to Azure App Service for public access

---

## 👤 Author

**Anirudh Varshney**
- Microsoft Certified: Azure AI Fundamentals (AI-900)
- Summer Training Project 2026

---

## 📄 License

This project is built for educational purposes as part of Summer Training 2026.
