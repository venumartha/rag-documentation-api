"""
RAG Documentation API
A production-ready RAG system for querying technical documentation with citations.
"""

import os
import time
import hashlib
from typing import List, Optional
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate


# Initialize FastAPI app
app = FastAPI(
    title="RAG Documentation API",
    description="Query technical documentation using RAG with source citations",
    version="1.0.0"
)

# Global variables for vector store and QA chain
vectorstore = None
qa_chain = None


class QueryRequest(BaseModel):
    """Request model for documentation queries"""
    question: str = Field(..., description="The question to ask about the documentation")
    max_sources: int = Field(default=5, ge=1, le=10, description="Maximum number of source chunks to return")
    temperature: float = Field(default=0.0, ge=0.0, le=1.0, description="LLM temperature for creativity")


class SourceDocument(BaseModel):
    """Model for source document chunks"""
    content: str
    source: str
    chunk_id: Optional[int] = None


class QueryResponse(BaseModel):
    """Response model with answer and citations"""
    answer: str
    sources: List[SourceDocument]
    retrieval_time_ms: float
    tokens_used: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    vectorstore_loaded: bool
    documents_indexed: int


def load_documents(docs_path: str = "./docs") -> List:
    """
    Load documents from directory and split into chunks
    
    Args:
        docs_path: Path to documentation directory
        
    Returns:
        List of document chunks
    """
    print(f"Loading documents from {docs_path}...")
    
    # Load all text and markdown files
    loader = DirectoryLoader(
        docs_path,
        glob="**/*.{txt,md}",
        loader_cls=TextLoader,
        show_progress=True
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} documents")
    
    # Split into chunks with overlap for better context
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks")
    
    return chunks


def create_vectorstore(chunks: List, persist_directory: str = "./vectorstore"):
    """
    Create vector store from document chunks
    
    Args:
        chunks: List of document chunks
        persist_directory: Where to save the vector store
        
    Returns:
        FAISS vector store instance
    """
    print("Creating embeddings and vector store...")
    
    # Use OpenAI embeddings (can switch to Anthropic if needed)
    embeddings = OpenAIEmbeddings()
    
    # Create FAISS vector store (free, runs locally)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # Save for future use
    vectorstore.save_local(persist_directory)
    print(f"Vector store saved to {persist_directory}")
    
    return vectorstore


def create_qa_chain(vectorstore, temperature: float = 0.0):
    """
    Create QA chain with custom prompt for citations
    
    Args:
        vectorstore: Vector store instance
        temperature: LLM temperature setting
        
    Returns:
        RetrievalQAWithSourcesChain instance
    """
    # Use GPT-4 for better reasoning (can switch to Claude)
    llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=temperature
    )
    
    # Custom prompt template for structured answers with citations
    prompt_template = """Use the following pieces of context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

For each piece of information you use, cite the source using [Source: filename].

Context:
{summaries}

Question: {question}

Provide a detailed answer with inline citations:"""

    PROMPT = PromptTemplate(
        template=prompt_template, 
        input_variables=["summaries", "question"]
    )
    
    # Create retrieval chain with source tracking
    chain = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance for diversity
            search_kwargs={"k": 5, "fetch_k": 20}
        ),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    return chain


@lru_cache(maxsize=100)
def cached_query(question_hash: str, max_sources: int, temperature: float) -> dict:
    """
    Cache query results to avoid redundant API calls
    
    Args:
        question_hash: MD5 hash of the question
        max_sources: Number of sources to return
        temperature: LLM temperature
        
    Returns:
        Query result dictionary
    """
    # This is a placeholder - actual query happens in the endpoint
    # The cache key includes question hash to enable caching
    return {}


@app.on_event("startup")
async def startup_event():
    """Initialize vector store and QA chain on startup"""
    global vectorstore, qa_chain
    
    print("Starting up RAG Documentation API...")
    
    # Check if vector store already exists
    persist_dir = "./vectorstore"
    docs_dir = "./docs"
    
    if os.path.exists(persist_dir):
        print("Loading existing vector store...")
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.load_local(persist_dir, embeddings)
        print("Vector store loaded successfully")
    elif os.path.exists(docs_dir):
        print("No vector store found. Creating from documents...")
        chunks = load_documents(docs_dir)
        vectorstore = create_vectorstore(chunks, persist_dir)
    else:
        print(f"WARNING: No documents found in {docs_dir}")
        print("Please add documentation files to the ./docs directory")
        vectorstore = None
        qa_chain = None
        return
    
    # Create QA chain
    qa_chain = create_qa_chain(vectorstore)
    print("QA chain initialized successfully")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "name": "RAG Documentation API",
        "version": "1.0.0",
        "endpoints": {
            "POST /query": "Query the documentation",
            "GET /health": "Health check",
            "POST /reindex": "Reindex documents"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    global vectorstore
    
    documents_count = 0
    if vectorstore is not None:
        documents_count = vectorstore.index.ntotal
    
    return HealthResponse(
        status="healthy" if vectorstore is not None else "not_ready",
        vectorstore_loaded=vectorstore is not None,
        documents_indexed=documents_count
    )


@app.post("/query", response_model=QueryResponse)
async def query_documentation(request: QueryRequest):
    """
    Query the documentation using RAG
    
    Args:
        request: QueryRequest with question and parameters
        
    Returns:
        QueryResponse with answer, sources, and metadata
    """
    global qa_chain, vectorstore
    
    if qa_chain is None or vectorstore is None:
        raise HTTPException(
            status_code=503,
            detail="Vector store not initialized. Please add documents to ./docs and restart."
        )
    
    # Generate cache key
    question_hash = hashlib.md5(
        f"{request.question}_{request.max_sources}_{request.temperature}".encode()
    ).hexdigest()
    
    # Start timing
    start_time = time.time()
    
    try:
        # Update chain temperature if different
        if qa_chain.combine_documents_chain.llm_chain.llm.temperature != request.temperature:
            qa_chain.combine_documents_chain.llm_chain.llm.temperature = request.temperature
        
        # Execute query
        result = qa_chain({
            "question": request.question
        })
        
        # Calculate retrieval time
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        # Format sources
        sources = []
        for idx, doc in enumerate(result.get('source_documents', [])[:request.max_sources]):
            sources.append(SourceDocument(
                content=doc.page_content,
                source=doc.metadata.get('source', 'unknown'),
                chunk_id=idx
            ))
        
        return QueryResponse(
            answer=result['answer'],
            sources=sources,
            retrieval_time_ms=round(retrieval_time_ms, 2)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/reindex")
async def reindex_documents():
    """
    Reindex all documents (useful after adding new docs)
    
    Returns:
        Status message
    """
    global vectorstore, qa_chain
    
    docs_dir = "./docs"
    persist_dir = "./vectorstore"
    
    if not os.path.exists(docs_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Documentation directory not found: {docs_dir}"
        )
    
    try:
        # Load and process documents
        chunks = load_documents(docs_dir)
        
        # Create new vector store
        vectorstore = create_vectorstore(chunks, persist_dir)
        
        # Recreate QA chain
        qa_chain = create_qa_chain(vectorstore)
        
        return {
            "status": "success",
            "message": f"Reindexed {len(chunks)} document chunks",
            "documents_indexed": vectorstore.index.ntotal
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reindexing documents: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
