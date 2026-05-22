# RAG System Tutorial - Understanding the Code

This guide walks through the entire RAG implementation to help you understand how it works.

## 📚 Table of Contents
1. [What is RAG?](#what-is-rag)
2. [Architecture Overview](#architecture-overview)
3. [Code Walkthrough](#code-walkthrough)
4. [Key Concepts](#key-concepts)
5. [Hands-On Exercises](#hands-on-exercises)

---

## What is RAG?

**Retrieval-Augmented Generation** combines:
- **Retrieval**: Finding relevant information from a knowledge base
- **Generation**: Using an LLM to create answers based on retrieved context

### Why RAG?
- LLMs have knowledge cutoff dates
- LLMs can hallucinate facts
- Your private data isn't in the training set
- RAG grounds answers in your actual documents

### RAG vs Fine-Tuning
| Aspect | RAG | Fine-Tuning |
|--------|-----|-------------|
| Update knowledge | Add new docs instantly | Retrain entire model |
| Cost | Low (embedding only) | High (GPU hours) |
| Transparency | Shows sources | Black box |
| Use case | Dynamic knowledge | Task-specific behavior |

---

## Architecture Overview

### The RAG Pipeline

```
1. INDEXING (One-time setup)
   Documents → Chunks → Embeddings → Vector Store

2. RETRIEVAL (Per query)
   Query → Embedding → Similar chunks → Top K results

3. GENERATION (Per query)
   Query + Retrieved chunks → LLM → Answer with citations
```

### Components in This Project

```python
# 1. Document Loading
DirectoryLoader → loads .md/.txt files
TextSplitter → breaks into chunks with overlap

# 2. Embedding
OpenAIEmbeddings → converts text to vectors (1536 dimensions)

# 3. Vector Store
FAISS → efficient similarity search (free, local)

# 4. Retrieval
MMR (Maximum Marginal Relevance) → diverse results
k=5 → return top 5 chunks
fetch_k=20 → initial candidates for diversity

# 5. LLM
GPT-4 → generate answer
Custom prompt → enforce citations
```

---

## Code Walkthrough

### Part 1: Document Loading (`load_documents`)

```python
def load_documents(docs_path: str = "./docs") -> List:
    # Load all .md and .txt files
    loader = DirectoryLoader(
        docs_path,
        glob="**/*.{txt,md}",
        loader_cls=TextLoader
    )
    documents = loader.load()
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # ~200 words per chunk
        chunk_overlap=200,    # Overlap prevents context loss
        separators=["\n\n", "\n", " ", ""]  # Split hierarchy
    )
    chunks = text_splitter.split_documents(documents)
    
    return chunks
```

**Why chunking?**
- Embeddings work on fixed-size inputs
- Smaller chunks = more precise retrieval
- Overlap preserves context across boundaries

**Chunk size tradeoff:**
- Too small (100): Loses context, many chunks
- Too large (5000): Generic matches, less relevant
- Sweet spot (800-1200): Good balance

### Part 2: Vector Store Creation (`create_vectorstore`)

```python
def create_vectorstore(chunks: List):
    # Create embeddings
    embeddings = OpenAIEmbeddings()  # text-embedding-ada-002
    
    # Build FAISS index
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Save to disk
    vectorstore.save_local("./vectorstore")
    
    return vectorstore
```

**What happens here?**
1. Each chunk → API call → 1536-dimensional vector
2. Vectors stored in FAISS index (efficient nearest-neighbor search)
3. Index saved to disk for reuse

**Cost estimate:**
- 1000 chunks × ~250 tokens/chunk = 250K tokens
- Embedding cost: $0.0001 per 1K tokens
- Total: ~$0.025 (one-time cost)

### Part 3: QA Chain Setup (`create_qa_chain`)

```python
def create_qa_chain(vectorstore, temperature: float = 0.0):
    # LLM for answer generation
    llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=temperature  # 0 = deterministic
    )
    
    # Custom prompt template
    prompt_template = """Use the following context to answer.
    Cite sources using [Source: filename].
    
    Context: {summaries}
    Question: {question}
    
    Answer with citations:"""
    
    # Build retrieval chain
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(
            search_type="mmr",  # Diverse results
            search_kwargs={"k": 5, "fetch_k": 20}
        ),
        return_source_documents=True
    )
    
    return chain
```

**Key parameters:**

**Temperature:**
- 0.0 = Deterministic, factual (use for docs)
- 0.7 = Creative (use for content generation)
- 1.0 = Very creative (use for brainstorming)

**MMR vs Similarity:**
- Similarity: Top 5 most similar chunks (may be redundant)
- MMR: Top 5 diverse chunks (covers more topics)

**k and fetch_k:**
- fetch_k=20: Get 20 candidates
- MMR selects k=5 diverse ones from those 20
- Higher fetch_k = more diversity, slower

### Part 4: Query Processing (FastAPI endpoint)

```python
@app.post("/query")
async def query_documentation(request: QueryRequest):
    # Execute query
    result = qa_chain({
        "question": request.question
    })
    
    # result contains:
    # - answer: LLM-generated response
    # - source_documents: Retrieved chunks
    # - sources: File names
    
    return QueryResponse(
        answer=result['answer'],
        sources=[...],  # Formatted sources
        retrieval_time_ms=...
    )
```

**What happens during a query?**

1. **User question** → "How do I optimize Lambda cold starts?"
2. **Embedding** → Convert question to 1536-dim vector
3. **Similarity search** → Find 20 similar chunks in FAISS
4. **MMR selection** → Pick 5 diverse chunks
5. **Prompt construction** → Insert chunks + question into template
6. **LLM generation** → GPT-4 creates answer with citations
7. **Response** → Return answer + source metadata

---

## Key Concepts

### 1. Embeddings

Embeddings convert text to numbers that capture semantic meaning:

```
"Lambda cold start" → [0.234, -0.567, 0.891, ...]
"Startup latency"   → [0.221, -0.544, 0.903, ...]  # Similar!
"Pizza recipe"      → [-0.789, 0.123, -0.456, ...] # Different!
```

**How similarity works:**
- Cosine similarity between vectors
- Range: -1 (opposite) to 1 (identical)
- Threshold: Usually >0.7 is relevant

### 2. Vector Databases

Why not just store in PostgreSQL?

```
# Naive approach (SLOW)
for each document:
    similarity = cosine(query_vector, doc_vector)
    if similarity > threshold:
        results.append(doc)

# FAISS approach (FAST)
# Uses k-d trees, product quantization, clustering
results = faiss_index.search(query_vector, k=5)
# 1000x faster for large datasets
```

### 3. Prompt Engineering for RAG

Bad prompt:
```
Answer: {question}
```
Problems: No context, no citations, hallucinations

Good prompt (our template):
```
Context: {summaries}
Question: {question}

Use the context to answer. Cite sources.
If you don't know, say so.
```
Benefits: Grounded, traceable, honest

### 4. Chunking Strategies

**Naive chunking:**
```python
# Split every 1000 chars
chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
```
Problems: Cuts mid-sentence, loses meaning

**Recursive chunking (our approach):**
```python
# Try to split on:
1. Double newline (paragraphs)
2. Single newline (sentences)
3. Spaces (words)
4. Characters (last resort)
```
Benefits: Preserves semantic units

---

## Hands-On Exercises

### Exercise 1: Add Your Own Documents

1. **Create a document:**
```bash
cat > docs/my_notes.md << 'EOF'
# My AWS Notes

## S3 Best Practices
- Use S3 Intelligent-Tiering for cost optimization
- Enable versioning for critical data
- Use lifecycle policies to move old data to Glacier

## DynamoDB Tips
- Use partition keys with high cardinality
- Enable point-in-time recovery for production
- Use DynamoDB Streams for change data capture
EOF
```

2. **Reindex:**
```bash
curl -X POST http://localhost:8000/reindex
```

3. **Test query:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are S3 best practices?"}'
```

### Exercise 2: Tune Chunk Size

Experiment with different chunk sizes in `main.py`:

```python
# Original
chunk_size=1000, chunk_overlap=200

# Try these:
chunk_size=500, chunk_overlap=100   # Smaller, more precise
chunk_size=2000, chunk_overlap=400  # Larger, more context
```

After each change:
1. Delete `./vectorstore` directory
2. Restart API (it will reindex)
3. Run `python evaluate.py`
4. Compare relevance scores and latency

### Exercise 3: Switch to Claude

Replace GPT-4 with Claude in `main.py`:

```python
# Before
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(model_name="gpt-4", temperature=temperature)

# After
from langchain.chat_models import ChatAnthropic
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=temperature
)
```

Don't forget to set `ANTHROPIC_API_KEY` in `.env`

Compare:
- Answer quality
- Citation format
- Cost (Claude is cheaper)
- Latency

### Exercise 4: Add Conversation Memory

Currently each query is independent. Add memory:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    memory=memory
)
```

Now you can ask follow-ups:
```
User: "How do I optimize Lambda?"
AI: "Use provisioned concurrency..."

User: "What about cost?"  # Understands context!
AI: "Provisioned concurrency costs $X per GB-hour..."
```

### Exercise 5: Hybrid Search

Add keyword search alongside semantic:

```python
from langchain.retrievers import BM25Retriever, EnsembleRetriever

# Semantic retriever (current)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Keyword retriever (new)
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 5

# Combine both
ensemble_retriever = EnsembleRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    weights=[0.7, 0.3]  # 70% semantic, 30% keyword
)

# Use in chain
chain = RetrievalQAWithSourcesChain.from_chain_type(
    llm=llm,
    retriever=ensemble_retriever,  # <-- Changed
    ...
)
```

Benefits:
- Catches exact term matches
- More robust to typos
- Better for technical terms

---

## Debugging Tips

### Check embeddings quality:
```python
# In Python shell
from langchain.embeddings import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()

# Embed two similar texts
vec1 = embeddings.embed_query("Lambda cold start optimization")
vec2 = embeddings.embed_query("Reducing Lambda startup time")

# Calculate similarity
import numpy as np
similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
print(f"Similarity: {similarity:.3f}")  # Should be >0.8
```

### Inspect retrieved chunks:
```python
# Add logging in main.py
result = qa_chain({"question": request.question})

print("Retrieved chunks:")
for i, doc in enumerate(result['source_documents']):
    print(f"\n[{i}] {doc.metadata['source']}")
    print(doc.page_content[:200])
```

### Test different retrieval strategies:
```python
# Try similarity instead of MMR
retriever=vectorstore.as_retriever(
    search_type="similarity",  # Changed from mmr
    search_kwargs={"k": 5}
)
```

---

## Common Issues & Solutions

**Issue: Slow queries (>2 seconds)**
- Solution: Reduce fetch_k from 20 to 10
- Solution: Use smaller chunk_size
- Solution: Enable query caching

**Issue: Irrelevant answers**
- Solution: Increase chunk_overlap
- Solution: Use MMR instead of similarity
- Solution: Add more diverse documents

**Issue: High OpenAI costs**
- Solution: Cache embeddings (done automatically)
- Solution: Switch to Claude (cheaper)
- Solution: Use smaller chunk_size (fewer embeddings)

**Issue: Missing citations**
- Solution: Update prompt to emphasize citations
- Solution: Increase k to retrieve more sources
- Solution: Use temperature=0 for deterministic output

---

## Next Steps

1. **Production deployment:**
   - Add authentication (JWT)
   - Set up rate limiting
   - Deploy to AWS Lambda + API Gateway
   - Use managed vector DB (Pinecone/Weaviate)

2. **Advanced features:**
   - Multi-modal RAG (PDFs, images)
   - Agentic RAG (self-correcting)
   - Graph RAG (entity relationships)
   - Long-context RAG (100K+ tokens)

3. **Monitoring:**
   - LangSmith for tracing
   - Prometheus metrics
   - User feedback loops
   - A/B testing retrievers

---

**Questions?** Open an issue on GitHub!
