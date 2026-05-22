"""
RAG Evaluation Script
Tests the quality and performance of the RAG system
"""

import time
import json
import requests
from typing import List, Dict
from statistics import mean, median


# Test questions with expected topics
TEST_QUESTIONS = [
    {
        "question": "How do I optimize AWS Lambda cold starts?",
        "expected_topics": ["provisioned concurrency", "snapstart", "vpc", "memory"],
        "category": "performance"
    },
    {
        "question": "What are the best practices for Kafka stream processing?",
        "expected_topics": ["exactly-once", "stateful", "windowing", "changelog"],
        "category": "streaming"
    },
    {
        "question": "How do I secure API endpoints with JWT?",
        "expected_topics": ["authentication", "token", "validation", "claims"],
        "category": "security"
    },
    {
        "question": "What's the difference between DynamoDB and PostgreSQL?",
        "expected_topics": ["nosql", "relational", "query", "scaling"],
        "category": "databases"
    },
    {
        "question": "How do I implement distributed tracing?",
        "expected_topics": ["opentelemetry", "spans", "context", "propagation"],
        "category": "observability"
    }
]


class RAGEvaluator:
    """Evaluates RAG system performance and quality"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.results = []
    
    def check_health(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(f"{self.api_url}/health")
            return response.status_code == 200 and response.json()["status"] == "healthy"
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def query(self, question: str, max_sources: int = 5) -> Dict:
        """Send query to RAG API"""
        try:
            response = requests.post(
                f"{self.api_url}/query",
                json={
                    "question": question,
                    "max_sources": max_sources,
                    "temperature": 0.0
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Query failed: {e}")
            return None
    
    def evaluate_relevance(self, answer: str, expected_topics: List[str]) -> float:
        """
        Simple relevance score based on topic coverage
        Returns: 0.0 to 1.0
        """
        answer_lower = answer.lower()
        matches = sum(1 for topic in expected_topics if topic.lower() in answer_lower)
        return matches / len(expected_topics)
    
    def evaluate_citations(self, sources: List[Dict]) -> Dict:
        """Evaluate citation quality"""
        return {
            "source_count": len(sources),
            "has_sources": len(sources) > 0,
            "avg_chunk_length": mean([len(s["content"]) for s in sources]) if sources else 0
        }
    
    def run_evaluation(self) -> Dict:
        """Run full evaluation suite"""
        print("=" * 60)
        print("RAG EVALUATION STARTING")
        print("=" * 60)
        
        # Check health
        if not self.check_health():
            print("❌ API is not healthy. Aborting evaluation.")
            return None
        
        print("✅ API is healthy\n")
        
        # Run test questions
        latencies = []
        relevance_scores = []
        citation_counts = []
        
        for idx, test in enumerate(TEST_QUESTIONS, 1):
            print(f"\n[{idx}/{len(TEST_QUESTIONS)}] Category: {test['category']}")
            print(f"Question: {test['question']}")
            
            # Query API
            result = self.query(test["question"])
            
            if not result:
                print("❌ Query failed")
                continue
            
            # Collect metrics
            latency = result["retrieval_time_ms"]
            relevance = self.evaluate_relevance(result["answer"], test["expected_topics"])
            citation_info = self.evaluate_citations(result["sources"])
            
            latencies.append(latency)
            relevance_scores.append(relevance)
            citation_counts.append(citation_info["source_count"])
            
            # Display results
            print(f"  ⏱️  Latency: {latency:.0f}ms")
            print(f"  🎯 Relevance: {relevance:.2%}")
            print(f"  📚 Sources: {citation_info['source_count']}")
            print(f"  📝 Answer preview: {result['answer'][:150]}...")
            
            # Store full result
            self.results.append({
                "question": test["question"],
                "category": test["category"],
                "latency_ms": latency,
                "relevance_score": relevance,
                "source_count": citation_info["source_count"],
                "answer": result["answer"],
                "sources": result["sources"]
            })
        
        # Calculate aggregate metrics
        print("\n" + "=" * 60)
        print("EVALUATION SUMMARY")
        print("=" * 60)
        
        metrics = {
            "total_queries": len(TEST_QUESTIONS),
            "successful_queries": len(latencies),
            "latency": {
                "mean_ms": round(mean(latencies), 2),
                "median_ms": round(median(latencies), 2),
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
                "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 2)
            },
            "relevance": {
                "mean_score": round(mean(relevance_scores), 3),
                "median_score": round(median(relevance_scores), 3),
                "min_score": round(min(relevance_scores), 3),
                "max_score": round(max(relevance_scores), 3)
            },
            "citations": {
                "mean_sources": round(mean(citation_counts), 1),
                "median_sources": median(citation_counts),
                "min_sources": min(citation_counts),
                "max_sources": max(citation_counts)
            }
        }
        
        print(f"\n📊 Performance Metrics:")
        print(f"  Mean Latency: {metrics['latency']['mean_ms']}ms")
        print(f"  Median Latency: {metrics['latency']['median_ms']}ms")
        print(f"  P95 Latency: {metrics['latency']['p95_ms']}ms")
        
        print(f"\n🎯 Quality Metrics:")
        print(f"  Mean Relevance: {metrics['relevance']['mean_score']:.2%}")
        print(f"  Mean Sources per Query: {metrics['citations']['mean_sources']}")
        
        # Save results
        with open("evaluation_results.json", "w") as f:
            json.dump({
                "metrics": metrics,
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n✅ Results saved to evaluation_results.json")
        print("=" * 60)
        
        return metrics


if __name__ == "__main__":
    evaluator = RAGEvaluator()
    metrics = evaluator.run_evaluation()
    
    if metrics:
        # Grade the system
        avg_relevance = metrics["relevance"]["mean_score"]
        avg_latency = metrics["latency"]["mean_ms"]
        
        print("\n🏆 FINAL GRADE:")
        
        if avg_relevance >= 0.8 and avg_latency < 500:
            print("  Grade: A (Production Ready)")
        elif avg_relevance >= 0.7 and avg_latency < 1000:
            print("  Grade: B (Good Performance)")
        elif avg_relevance >= 0.6:
            print("  Grade: C (Needs Optimization)")
        else:
            print("  Grade: D (Requires Improvement)")
