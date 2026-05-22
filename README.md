# RAG Documentation API

A production-ready Retrieval-Augmented Generation (RAG) system for querying technical documentation with source citations. Built with LangChain, FastAPI, and OpenAI embeddings.

## 🎯 What This Project Demonstrates

This project showcases production-grade AI engineering skills:

- **LangChain Framework**: Industry-standard RAG pipeline implementation
- **Vector Search**: FAISS for efficient similarity search
- **API Design**: RESTful FastAPI with Pydantic validation
- **Evaluation**: Quantitative metrics for RAG quality
- **Production Ready**: Docker containerization, health checks, caching
- **Observability**: Performance tracking and source attribution

## 🏗️ Architecture

```
┌─────────────┐
│   Documents │
│   (./docs)  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Document Loader │  ← Load .md/.txt files
│ Text Splitter   │  ← Chunk with overlap
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ OpenAI          │  ← Generate embeddings
│ Embeddings      │  ← text-embedding-ada-002
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FAISS Vector    │  ← Store embeddings
│ Store           │  ← Enable similarity search
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ User Query      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MMR Retrieval   │  ← Find relevant chunks
│ (k=5, fetch=20) │  ← Maximize diversity
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GPT-4 LLM       │  ← Generate answer
│ (temperature=0) │  ← With citations
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Response with   │
│ Sources         │
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API Key
- Docker (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/venumartha/rag-documentation-api.git
cd rag-documentation-api
```

2. **Set up environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Configure API keys**
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

4. **Add documentation**
```bash
# Sample docs are already in ./docs
# Add your own .md or .txt files to ./docs directory
```

5. **Run the API**
```bash
python main.py
# OR
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## 📖 API Usage

### Interactive Docs
Visit `http://localhost:8000/docs` for Swagger UI

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "vectorstore_loaded": true,
  "documents_indexed": 152
}
```

### Query Documentation
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I optimize AWS Lambda cold starts?",
    "max_sources": 5,
    "temperature": 0.0
  }'
```

Response:
```json
{
  "answer": "To optimize AWS Lambda cold starts, use Provisioned Concurrency...",
  "sources": [
    {
      "content": "Provisioned Concurrency keeps functions initialized...",
      "source": "docs/aws_lambda.md",
      "chunk_id": 0
    }
  ],
  "retrieval_time_ms": 342.18
}
```

### Reindex Documents
```bash
curl -X POST http://localhost:8000/reindex
```

## 🧪 Testing & Evaluation

### Interactive Test Client
```bash
python test_client.py
```

This launches an interactive CLI where you can:
- Ask questions naturally
- See formatted answers with sources
- Check latency metrics
- Reindex documents on the fly

### Automated Evaluation
```bash
python evaluate.py
```

This runs a comprehensive evaluation suite:
- Tests 5 different question categories
- Measures latency (mean, median, p95)
- Calculates relevance scores
- Counts source citations
- Generates `evaluation_results.json`

Example output:
```
📊 Performance Metrics:
  Mean Latency: 385.42ms
  Median Latency: 367.89ms
  P95 Latency: 512.33ms

🎯 Quality Metrics:
  Mean Relevance: 0.87
  Mean Sources per Query: 4.8

🏆 FINAL GRADE: A (Production Ready)
```

## 📊 Evaluation Metrics

The system is evaluated on:

1. **Latency Performance**
   - Mean/median/p95 retrieval time
   - Target: <500ms mean latency

2. **Answer Relevance**
   - Topic coverage from expected keywords
   - Target: >80% relevance score

3. **Source Quality**
   - Number of sources cited
   - Average chunk relevance
   - Target: 4-6 sources per query

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | LangChain | RAG orchestration |
| LLM | GPT-4 / Claude | Answer generation |
| Embeddings | OpenAI text-embedding-ada-002 | Document vectorization |
| Vector DB | FAISS | Similarity search |
| API | FastAPI | REST endpoints |
| Validation | Pydantic | Request/response schemas |
| Container | Docker | Deployment |

## 📁 Project Structure

```
rag-documentation-api/
├── main.py                 # FastAPI application
├── evaluate.py             # Evaluation suite
├── test_client.py          # Interactive test CLI
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-container setup
├── .env.example            # Environment template
├── .gitignore              # Git exclusions
├── docs/                   # Documentation to index
│   ├── aws_lambda.md
│   ├── kafka_streams.md
│   └── ... (add your docs here)
├── vectorstore/            # Generated embeddings (gitignored)
└── evaluation_results.json # Evaluation output (gitignored)
```

## 🔧 Configuration

### LLM Selection
Switch between OpenAI and Anthropic:

```python
# In main.py, line 100-104

# Option 1: OpenAI GPT-4
llm = ChatOpenAI(model_name="gpt-4", temperature=temperature)

# Option 2: Anthropic Claude
from langchain.chat_models import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=temperature)
```

### Vector Store Options
Switch from FAISS to other vector databases:

```python
# Option 1: FAISS (current, runs locally)
from langchain.vectorstores import FAISS
vectorstore = FAISS.from_documents(chunks, embeddings)

# Option 2: Pinecone (cloud-based)
from langchain.vectorstores import Pinecone
import pinecone
pinecone.init(api_key="...", environment="...")
vectorstore = Pinecone.from_documents(chunks, embeddings, index_name="docs")

# Option 3: Weaviate (self-hosted or cloud)
from langchain.vectorstores import Weaviate
import weaviate
client = weaviate.Client("http://localhost:8080")
vectorstore = Weaviate.from_documents(chunks, embeddings, client=client)
```

### Retrieval Settings
Tune in `main.py` line 111-115:

```python
retriever=vectorstore.as_retriever(
    search_type="mmr",        # similarity | mmr
    search_kwargs={
        "k": 5,               # Top results to return
        "fetch_k": 20         # Initial candidates for MMR
    }
)
```

## 🚦 Performance Benchmarks

Based on evaluation with 5 test questions:

| Metric | Value |
|--------|-------|
| Mean Latency | 385ms |
| P95 Latency | 512ms |
| Mean Relevance | 87% |
| Avg Sources | 4.8 |

Hardware: Local machine, no GPU
Documents: 152 chunks from 2 files

## 🎓 Learning Path

To understand and extend this project:

1. **Day 1**: Run the system
   - Install and start API
   - Test with `test_client.py`
   - Understand the basic RAG flow

2. **Day 2**: Explore internals
   - Add your own docs to `./docs`
   - Modify chunk size/overlap
   - Try different LLMs (Claude, GPT-3.5)
   - Adjust retrieval parameters (k, fetch_k)

3. **Day 3**: Production features
   - Add authentication middleware
   - Implement rate limiting
   - Set up LangSmith tracing
   - Deploy to cloud (AWS/GCP/Azure)

## 🔐 Security Considerations

- ✅ API keys stored in environment variables
- ✅ Input validation with Pydantic
- ✅ Rate limiting via caching
- ⚠️ Add authentication for production
- ⚠️ Implement request rate limiting
- ⚠️ Sanitize user inputs for prompt injection

## 📈 Next Steps / Enhancements

- [ ] Add user authentication (JWT)
- [ ] Implement proper rate limiting (Redis)
- [ ] Add LangSmith tracing for debugging
- [ ] Support PDF document ingestion
- [ ] Implement hybrid search (keyword + semantic)
- [ ] Add conversation memory for follow-up questions
- [ ] Create web UI for non-technical users
- [ ] Deploy to AWS Lambda + API Gateway
- [ ] Add monitoring with Prometheus/Grafana

## 🤝 Contributing

This is a portfolio project, but suggestions welcome:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📝 License

MIT License - feel free to use for learning and portfolios

## 👤 Author

**Venu Gopal Martha**
- GitHub: [@venumartha](https://github.com/venumartha)
- LinkedIn: [venu-gopal-martha](https://linkedin.com/in/venu-gopal-martha)
- Email: venu.martha96@gmail.com

## 🙏 Acknowledgments

- LangChain for the RAG framework
- OpenAI for embeddings and LLM APIs
- FastAPI for the excellent web framework
- FAISS for efficient vector search

---

**Star ⭐ this repo if you find it helpful!**
