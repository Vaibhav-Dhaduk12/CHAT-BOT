# 🔄 Change Website for Your Chatbot

Your AI chatbot is now flexible! You can easily configure it to work with any website. Here's how:

---

## ⚡ Quick Start (3 Steps)

### **Step 1: Open Configuration Page**
```
http://localhost:8000/config
```

### **Step 2: Enter New Website Details**
- **Website URL:** The homepage of the site you want to crawl
- **Chatbot ID:** A unique identifier (e.g., `my_company_bot`)
- **Max Pages:** How many pages to crawl (50 recommended)
- **Crawl Depth:** How deep to follow links (3 recommended)

### **Step 3: Copy & Run Command**
1. Click "Generate Command"
2. Click "Copy Command"
3. Paste in Terminal
4. Wait for indexing to complete

---

## 📝 Examples

### **Example 1: E-Commerce Website**
```
Website URL: https://www.example-shop.com
Chatbot ID: ecommerce_support_bot
Max Pages: 100
Crawl Depth: 3
```

**Generated Command:**
```bash
python run_pipeline.py \
  --url "https://www.example-shop.com" \
  --chatbot-id "ecommerce_support_bot" \
  --max-pages 100 \
  --max-depth 3
```

### **Example 2: SaaS Documentation**
```
Website URL: https://docs.myapp.com
Chatbot ID: docs_bot
Max Pages: 200
Crawl Depth: 5
```

### **Example 3: Company Website**
```
Website URL: https://company-site.com
Chatbot ID: company_support_bot
Max Pages: 50
Crawl Depth: 2
```

---

## 🎯 What Happens When You Run The Command

```
1. 🕷️  CRAWLING
   └─ Extracts content from all pages
   └─ Respects robots.txt
   └─ Saves raw HTML content
   
2. 📄 PROCESSING
   └─ Breaks content into chunks
   └─ Removes noise (ads, navigation)
   └─ Creates text segments
   
3. 🧠 EMBEDDING
   └─ Converts text to AI vectors
   └─ Uses HuggingFace model
   └─ Stores in FAISS database
   
4. ✅ READY
   └─ Chatbot automatically updated
   └─ Uses new knowledge base
   └─ Serving queries instantly
```

---

## 🌐 Multiple Websites

You can run **multiple chatbots** for different sites!

```bash
# Chatbot 1: Insurance Website
python run_pipeline.py --url "https://insurance-site.com" --chatbot-id "insurance_bot"

# Chatbot 2: E-Commerce Site
python run_pipeline.py --url "https://shop-site.com" --chatbot-id "ecommerce_bot"

# Chatbot 3: Documentation
python run_pipeline.py --url "https://docs-site.com" --chatbot-id "docs_bot"
```

**Query each one:**
```python
# Insurance bot
POST /api/query
{
  "query": "What are your policies?",
  "chatbot_id": "insurance_bot"
}

# E-commerce bot
POST /api/query
{
  "query": "What's the shipping cost?",
  "chatbot_id": "ecommerce_bot"
}

# Docs bot
POST /api/query
{
  "query": "How do I install this?",
  "chatbot_id": "docs_bot"
}
```

---

## 🎨 Customize Chatbot for Each Site

Each chatbot stores its data separately:

```
data/
├── raw/
│   ├── insurance_bot/          ← Raw crawled content
│   ├── ecommerce_bot/
│   └── docs_bot/
├── processed/
│   ├── insurance_bot/          ← Processed chunks
│   ├── ecommerce_bot/
│   └── docs_bot/
└── vectors/
    ├── insurance_bot.pkl       ← Embeddings FAISS index
    ├── ecommerce_bot.pkl
    └── docs_bot.pkl
```

---

## 📊 Monitor Indexing Progress

When you run a command, you'll see:

```
🤖 Initializing RAG Pipeline: my_new_bot
   URL: https://my-site.com
   Max Depth: 3, Max Pages: 50
   Embeddings: huggingface, Vector DB: faiss

===========================================================
📡 STEP 1: CRAWLING WEBSITE
===========================================================
Starting crawl from: https://my-site.com
✅ Crawling Complete!
   📄 Pages crawled: 47
   📊 Total characters: 750,000
   📁 Stored in: data/raw/my_new_bot/

===========================================================
📝 STEP 2: PROCESSING DOCUMENTS
===========================================================
✅ Processing Complete!
   ✂️  Chunks created: 2,100
   📊 Total characters: 800,000
   🔢 Total tokens: 215,000

===========================================================
🧠 STEP 3: GENERATING EMBEDDINGS & INDEXING
===========================================================
Embedding 2,100 chunks...
✅ Embedding Complete!
   🔢 Chunks indexed: 2,100
   📦 Embedding dimension: 384

✅ Pipeline successful in 5 minutes 23 seconds
```

---

## ⚙️ Configuration Page Features

```
┌─────────────────────────────────────┐
│  🤖 Chatbot Configuration           │
├─────────────────────────────────────┤
│                                     │
│  📊 Current Setup                   │
│  URL: viphub.phoenixins.mu          │
│  ID: phoenix_insurance_bot          │
│  Content: 1,453 chunks              │
│  Status: ✓ Ready                    │
│                                     │
│  🌐 Change Website                  │
│  [Website URL input field]          │
│  [Chatbot ID input field]           │
│  [Max Pages spinner]                │
│  [Crawl Depth spinner]              │
│                                     │
│  [Generate Command] [Copy Command]  │
│                                     │
│  🚀 Setup Instructions              │
│  1. Fill in website details         │
│  2. Click Generate Command          │
│  3. Copy command                    │
│  4. Run in Terminal                 │
│  5. Wait for indexing               │
│                                     │
│  [Open Chatbot] [API Docs]         │
└─────────────────────────────────────┘
```

---

## 🔐 Best Practices

### **URL Tips**
- ✅ Use homepage: `https://example.com`
- ✅ Use specific section: `https://example.com/help`
- ❌ Don't use subpaths you don't want: `https://example.com/admin`

### **Chatbot ID Tips**
- ✅ Lowercase with underscores: `company_support_bot`
- ✅ Descriptive: `product_faq_bot`, `technical_docs_bot`
- ❌ Don't use spaces or special chars

### **Performance Tips**
- 📈 Start small (50 pages) to test
- 📈 Increase max-pages for larger knowledge bases
- 📈 Set crawl-depth based on site structure
- ⏱️ Allow 5-15 minutes for full indexing

---

## 🆘 Troubleshooting

### **"No results found for query"**
- The chatbot might not have crawled the content
- Check Status on config page shows site is ready
- Re-run the pipeline with more pages

### **"Crawling too slow"**
- Try reducing max-pages
- Check your internet connection
- Websites with lots of large files are slower

### **"Connection refused"**
- Make sure server is running: `python start_server.py`
- Check port 8000 is available
- Try different port: `--port 8001`

### **"Out of memory"**
- Reduce max-pages to 25-30
- Process large sites in sections
- Make sure you have 4GB+ RAM

---

## 🔗 Links

- **Configuration**: http://localhost:8000/config
- **Chatbot**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Console Output**: Watch terminal for progress

---

## 💡 Pro Tips

1. **Test with small site first**
   ```bash
   python run_pipeline.py --url "https://test-site.com" \
     --chatbot-id "test_bot" --max-pages 10
   ```

2. **Re-index to update knowledge**
   Just run the pipeline again with same chatbot-id to replace old data

3. **Keep multiple chatbots**
   Each has separate knowledge base - perfect for multi-product companies

4. **Monitor in real-time**
   Watch the terminal output to see indexing progress

---

**Happy chatbot building! 🚀**
