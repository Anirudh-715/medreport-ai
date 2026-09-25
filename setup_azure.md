# Azure Setup Guide for MedReport AI

This guide walks you through creating the required Azure resources for the Medical Report Summarizer project.

> **Prerequisite**: You need an Azure account. If you have the **GitHub Student Developer Pack**, you get **Azure for Students** with **$100 free credit** — more than enough for this project.

---

## 🔑 Step 1: Sign in to Azure Portal

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with your Microsoft account
3. If using Azure for Students, activate it at [https://azure.microsoft.com/en-us/free/students/](https://azure.microsoft.com/en-us/free/students/)

---

## 📄 Step 2: Create Azure AI Document Intelligence Resource

1. In Azure Portal, click **"Create a resource"**
2. Search for **"Document Intelligence"** (or "Form Recognizer")
3. Click **Create**
4. Fill in:
   - **Subscription**: Your Azure subscription
   - **Resource group**: Create new → `medreport-ai-rg`
   - **Region**: `East US` (or nearest to you)
   - **Name**: `medreport-doc-intel` (must be unique)
   - **Pricing tier**: `Free F0` (500 pages/month — plenty for development)
5. Click **Review + Create** → **Create**
6. Once deployed, go to the resource
7. Click **"Keys and Endpoint"** in the left menu
8. Copy:
   - **Endpoint** → This is your `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
   - **KEY 1** → This is your `AZURE_DOCUMENT_INTELLIGENCE_KEY`

---

## 🤖 Step 3: Create Azure OpenAI Resource

> **Note**: Azure OpenAI requires approval. If you don't have access, you can apply at [https://aka.ms/oai/access](https://aka.ms/oai/access). Approval usually takes 1-2 business days for students.

1. In Azure Portal, click **"Create a resource"**
2. Search for **"Azure OpenAI"**
3. Click **Create**
4. Fill in:
   - **Subscription**: Your Azure subscription
   - **Resource group**: `medreport-ai-rg` (same as above)
   - **Region**: `East US` (check region availability)
   - **Name**: `medreport-openai` (must be unique)
   - **Pricing tier**: `Standard S0`
5. Click **Review + Create** → **Create**
6. Once deployed, go to the resource

### Deploy a GPT-4o Model
1. Go to **"Model deployments"** → **"Manage Deployments"**
2. This opens **Azure AI Foundry** (formerly Azure OpenAI Studio)
3. Click **"Create new deployment"**
4. Select:
   - **Model**: `gpt-4o`
   - **Deployment name**: `gpt-4o` (use this exact name)
   - **Deployment type**: Standard
5. Click **Create**

### Get Your Keys
1. Go back to your Azure OpenAI resource in Azure Portal
2. Click **"Keys and Endpoint"**
3. Copy:
   - **Endpoint** → This is your `AZURE_OPENAI_ENDPOINT`
   - **KEY 1** → This is your `AZURE_OPENAI_KEY`
   - **Deployment name** → This is your `AZURE_OPENAI_DEPLOYMENT_NAME` (should be `gpt-4o`)

---

## ☁️ Step 4: Create Azure Storage Account

1. In Azure Portal, click **"Create a resource"**
2. Search for **"Storage account"**
3. Click **Create**
4. Fill in:
   - **Subscription**: Your Azure subscription
   - **Resource group**: `medreport-ai-rg`
   - **Storage account name**: `medreportstorage` (lowercase, must be unique)
   - **Region**: `East US`
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally-redundant storage — cheapest)
5. Click **Review + Create** → **Create**
6. Once deployed, go to the resource
7. Click **"Access keys"** in the left menu
8. Click **"Show"** next to the connection string
9. Copy the **Connection string** → This is your `AZURE_STORAGE_CONNECTION_STRING`

---

## 📝 Step 5: Configure Your .env File

Copy the `.env.example` file to `.env`:

```bash
copy .env.example .env
```

Edit `.env` and paste in your values:

```env
# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://medreport-doc-intel.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-actual-key-here

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://medreport-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-actual-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-10-21

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=medreportstorage;...
AZURE_STORAGE_CONTAINER_NAME=medical-reports

# Flask
FLASK_SECRET_KEY=any-random-string-here
FLASK_DEBUG=True
```

---

## 💰 Cost Estimate

| Service | Free Tier | Estimated Monthly Cost |
|---------|-----------|----------------------|
| Document Intelligence | 500 pages/month FREE | $0 |
| Azure OpenAI (GPT-4o) | — | ~$1-5 for development |
| Blob Storage | 5 GB FREE | $0 |
| **Total** | | **< $5/month** |

With your **$100 Azure for Students credit**, this project will cost essentially nothing.

---

## ✅ Verification

After setting up everything, run the app and check the home page. If any services are not configured, the app will show a warning indicating which credentials are missing.

```bash
python run.py
```

Visit `http://127.0.0.1:5000` and the app should load without errors.

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|---------|
| "Azure OpenAI access denied" | Apply for access at [aka.ms/oai/access](https://aka.ms/oai/access) |
| "Module not found" errors | Run `pip install -r requirements.txt` |
| "Invalid API key" | Double-check your keys in `.env` — no extra spaces |
| "Region not supported" | Try `East US` or `West Europe` regions |
| Document Intelligence not extracting text | Make sure the PDF is not password-protected |
