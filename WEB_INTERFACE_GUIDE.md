# 🤖 Phoenix Insurance AI Chatbot - Web Interface Guide

Your AI chatbot is now ready to be deployed as a beautiful web interface! Here's how to set it up:

## 🚀 Quick Start (3 Steps)

### Step 1: Index Your Website Content
This creates the knowledge base for your chatbot:

```bash
python run_pipeline.py `
  --url "https://viphub.phoenixins.mu/" `
  --chatbot-id "phoenix_insurance_bot" `
  --max-pages 50 `
  --max-depth 3
```

**What this does:**
- 🕷️ Crawls 50 pages of your website
- 📄 Extracts insurance products, pricing, contact info
- 🧠 Generates AI embeddings (machine learning)
- 💾 Stores in vector database (FAISS)

**Output:**
```
✅ Crawling Complete! 26 pages crawled
✅ Processing Complete! 1,453 text chunks created
✅ Embedding Complete! 1,453 chunks indexed
```

---

### Step 2: Start the Web Server
Launch the beautiful chat interface:

#### **Option A: Using the Startup Script (Recommended)**
```bash
python start_server.py
```

#### **Option B: Manual Start with Uvicorn**
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 3: Visit the Chatbot
Open your browser to: **http://localhost:8000**

You should see:
```
🛡️ Phoenix Insurance AI Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Chat Interface]

Quick Questions:
  🛡️ Insurance Products
  💰 Pricing
  🛒 How to Buy
  📞 Contact Us

Status: ✓ Ready
Indexed Content: 1,453 chunks
```

---

## 📋 Features

### Chat Interface
✅ Beautiful, modern UI with sidebar  
✅ Quick question buttons  
✅ Real-time responses with sources  
✅ Message history  
✅ Mobile responsive  
✅ Dark/Light mode compatible  

### Question Examples
```
"What insurance products do you offer?"
"How much is car insurance?"
"What are the payment options?"
"How do I renew my policy?"
"What's your contact number?"
"Are there any discounts available?"
```

---

## 🔧 API Endpoints

If you want to integrate with your own frontend:

### Query Endpoint
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What insurance products do you offer?",
    "chatbot_id": "phoenix_insurance_bot",
    "top_k": 4
  }'
```

**Response:**
```json
{
  "query": "What insurance products do you offer?",
  "results": [
    {
      "rank": 1,
      "text": "Motor Bike insurance from 1,575 MUR...",
      "source_url": "https://viphub.phoenixins.mu/...",
      "page_title": "Motor Bike Insurance",
      "distance": 0.45
    }
  ],
  "total_results": 4
}
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Get Chatbot Stats
```bash
curl http://localhost:8000/api/chatbots/phoenix_insurance_bot/stats
```

---

## 🌐 Deployment Options

### Option 1: Local Network (Internal Company Use)
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```
Access from other computers: `http://<your-ip>:8000`

### Option 2: Production Server (AWS/DigitalOcean/etc)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m pip install gunicorn
   ```

2. **Run with Gunicorn:**
   ```bash
   gunicorn api.main:app `
     --workers 4 `
     --worker-class uvicorn.workers.UvicornWorker `
     --bind 0.0.0.0:8000
   ```

3. **Use Nginx as reverse proxy**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Option 3: Embed in Your Existing Website

Add this to your website's HTML:
```html
<div id="chatbot-container"></div>
<script>
  fetch('http://your-server:8000/')
    .then(r => r.text())
    .then(html => {
      document.getElementById('chatbot-container').innerHTML = html;
    });
</script>
```

Or use an iframe:
```html
<iframe 
  src="http://your-server:8000" 
  width="100%" 
  height="600px"
  style="border: none; border-radius: 10px;">
</iframe>
```

---

## 📊 How It Works (Under the Hood)

```
User Question
    ↓
[Web Interface] 
    ↓ (HTTP POST request)
[FastAPI Server]
    ↓
[EmbeddingManager]
    ├─ Convert question to 384-dim vector (HuggingFace model)
    ├─ Search FAISS database
    └─ Return top 4 most relevant chunks
    ↓
[Response Formatter]
    ├─ Extract key information
    ├─ Add sources and links
    └─ Format for display
    ↓
[Web Interface]
    └─ Display results with citations
```

---

## 🐛 Troubleshooting

### "Embedding manager not initialized"
Make sure you ran the pipeline first:
```bash
python run_pipeline.py --chatbot-id phoenix_insurance_bot --url https://viphub.phoenixins.mu/
```

### "Port 8000 already in use"
Use a different port:
```bash
python -m uvicorn api.main:app --port 8001
```

### "CORS errors in browser console"
Install cors middleware:
```bash
pip install fastapi-cors
```

Update api/main.py:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### "No results found"
The knowledge base might be empty. Check:
```bash
dir data\processed\phoenix_insurance_bot\
```

Should show: `chunks_index.json`

---

## 📞 Support

For questions about the chatbot:
- Check [PIPELINE_USAGE.md](./PIPELINE_USAGE.md) for crawling help
- Check [README.md](./README.md) for system setup

---

## 🎯 Next Steps

1. ✅ Run the pipeline to index content
2. ✅ Start the web server
3. ✅ Test the chat interface
4. ⏳ Deploy to production server
5. ⏳ Embed in your website
6. ⏳ Train team on chatbot capabilities
7. ⏳ Monitor performance and feedback

---

**Happy chatting! 🤖💬**
