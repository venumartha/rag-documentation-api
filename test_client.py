"""
Interactive Test Client for RAG Documentation API
Run this to test queries manually
"""

import requests
import json
from typing import Optional


class RAGClient:
    """Simple client for interacting with RAG API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def query(self, question: str, max_sources: int = 5, temperature: float = 0.0) -> Optional[dict]:
        """Send a query to the RAG API"""
        try:
            response = requests.post(
                f"{self.base_url}/query",
                json={
                    "question": question,
                    "max_sources": max_sources,
                    "temperature": temperature
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None
    
    def health_check(self) -> Optional[dict]:
        """Check API health status"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None
    
    def reindex(self) -> Optional[dict]:
        """Trigger document reindexing"""
        try:
            response = requests.post(f"{self.base_url}/reindex")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return None
    
    def display_result(self, result: dict):
        """Pretty print query result"""
        print("\n" + "=" * 80)
        print("ANSWER")
        print("=" * 80)
        print(result["answer"])
        
        print(f"\n⏱️  Retrieval Time: {result['retrieval_time_ms']:.2f}ms")
        
        print("\n" + "=" * 80)
        print(f"SOURCES ({len(result['sources'])})")
        print("=" * 80)
        
        for idx, source in enumerate(result["sources"], 1):
            print(f"\n[{idx}] {source['source']}")
            print(f"    {source['content'][:200]}...")
        
        print("\n" + "=" * 80)


def main():
    """Interactive CLI"""
    client = RAGClient()
    
    print("=" * 80)
    print("RAG DOCUMENTATION API - TEST CLIENT")
    print("=" * 80)
    
    # Health check
    print("\nChecking API health...")
    health = client.health_check()
    if health:
        print(f"✅ Status: {health['status']}")
        print(f"📚 Documents Indexed: {health['documents_indexed']}")
    else:
        print("❌ API is not responding")
        return
    
    print("\nCommands:")
    print("  - Type your question to query the documentation")
    print("  - Type 'reindex' to reindex documents")
    print("  - Type 'exit' to quit")
    
    # Interactive loop
    while True:
        print("\n" + "-" * 80)
        user_input = input("\nQuestion: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
        
        if user_input.lower() == 'reindex':
            print("\nReindexing documents...")
            result = client.reindex()
            if result:
                print(f"✅ {result['message']}")
            continue
        
        # Query the API
        result = client.query(user_input)
        
        if result:
            client.display_result(result)


# Example queries to try
EXAMPLE_QUERIES = [
    "How do I optimize AWS Lambda cold starts?",
    "What are the best practices for Kafka stream processing?",
    "How do I implement JWT authentication?",
    "What's the difference between DynamoDB and PostgreSQL?",
    "How do I set up distributed tracing with OpenTelemetry?",
    "What are common patterns for handling errors in microservices?",
    "How do I implement rate limiting in FastAPI?",
]


if __name__ == "__main__":
    print("\n💡 Example queries you can try:")
    for idx, query in enumerate(EXAMPLE_QUERIES, 1):
        print(f"  {idx}. {query}")
    print()
    
    main()
