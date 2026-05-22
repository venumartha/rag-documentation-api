# Deployment Guide

This guide covers deploying the RAG API to various platforms.

## 🐳 Docker Deployment

### Local Docker

```bash
# Build image
docker build -t rag-api:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key-here \
  -v $(pwd)/docs:/app/docs \
  -v $(pwd)/vectorstore:/app/vectorstore \
  --name rag-api \
  rag-api:latest

# View logs
docker logs -f rag-api

# Stop
docker stop rag-api
docker rm rag-api
```

### Docker Compose

```bash
# Create .env file with API key
echo "OPENAI_API_KEY=your-key" > .env

# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## ☁️ AWS Deployment

### Option 1: AWS Lambda + API Gateway

**Benefits:** Serverless, auto-scaling, pay-per-request

**Setup:**

1. **Create Lambda Layer for dependencies:**
```bash
# Create layer directory
mkdir python
pip install -r requirements.txt -t python/
zip -r layer.zip python/

# Upload to Lambda Layers
aws lambda publish-layer-version \
  --layer-name rag-dependencies \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

2. **Package and deploy function:**
```bash
# Create deployment package
zip -r function.zip main.py

# Create Lambda function
aws lambda create-function \
  --function-name rag-documentation-api \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
  --handler main.handler \
  --zip-file fileb://function.zip \
  --timeout 30 \
  --memory-size 2048 \
  --environment Variables={OPENAI_API_KEY=your-key} \
  --layers arn:aws:lambda:region:account:layer:rag-dependencies:1
```

3. **Create API Gateway:**
```bash
# Create REST API
aws apigateway create-rest-api --name rag-api

# Configure routes to Lambda
# (Use AWS Console for easier setup)
```

**Cost estimate:**
- $0.20 per 1M requests
- $0.0000166667 per GB-second
- Typical query: ~$0.0001

### Option 2: ECS Fargate

**Benefits:** Container-based, long-running, easier debugging

**Setup:**

1. **Push to ECR:**
```bash
# Create ECR repository
aws ecr create-repository --repository-name rag-api

# Login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t rag-api .
docker tag rag-api:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/rag-api:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/rag-api:latest
```

2. **Create ECS Task Definition:**
```json
{
  "family": "rag-api-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "rag-api",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/rag-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "OPENAI_API_KEY",
          "value": "your-key-here"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/rag-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "rag"
        }
      }
    }
  ]
}
```

3. **Create ECS Service:**
```bash
aws ecs create-service \
  --cluster your-cluster \
  --service-name rag-api-service \
  --task-definition rag-api-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

**Cost estimate:**
- Fargate: ~$0.04/hour for 0.5 vCPU, 1GB RAM
- ~$30/month for 24/7 operation

---

## 🔵 Google Cloud Platform

### Cloud Run (Recommended)

**Benefits:** Serverless containers, auto-scaling, built-in HTTPS

**Setup:**

1. **Build and push to GCR:**
```bash
# Configure Docker for GCP
gcloud auth configure-docker

# Build
docker build -t gcr.io/YOUR_PROJECT/rag-api .

# Push
docker push gcr.io/YOUR_PROJECT/rag-api
```

2. **Deploy:**
```bash
gcloud run deploy rag-api \
  --image gcr.io/YOUR_PROJECT/rag-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=your-key \
  --memory 2Gi \
  --timeout 60s \
  --min-instances 0 \
  --max-instances 10
```

**Cost estimate:**
- $0.00002400 per vCPU-second
- $0.00000250 per GiB-second
- Free tier: 2M requests/month

---

## 🌊 Azure

### Azure Container Instances

**Setup:**

1. **Create container registry:**
```bash
az acr create --resource-group myResourceGroup \
  --name ragapiregistry --sku Basic
```

2. **Build and push:**
```bash
az acr build --registry ragapiregistry \
  --image rag-api:latest .
```

3. **Deploy:**
```bash
az container create \
  --resource-group myResourceGroup \
  --name rag-api \
  --image ragapiregistry.azurecr.io/rag-api:latest \
  --cpu 1 --memory 2 \
  --registry-login-server ragapiregistry.azurecr.io \
  --registry-username YOUR_USERNAME \
  --registry-password YOUR_PASSWORD \
  --dns-name-label rag-api-demo \
  --ports 8000 \
  --environment-variables OPENAI_API_KEY=your-key
```

---

## 🚀 Render.com (Easiest)

**Benefits:** Free tier, auto-deploy from GitHub, zero config

**Setup:**

1. Push code to GitHub
2. Go to render.com
3. Click "New Web Service"
4. Connect your GitHub repo
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** Add `OPENAI_API_KEY`
6. Deploy!

**Cost:** Free tier includes 750 hours/month

---

## 🔒 Production Checklist

Before deploying to production:

- [ ] Add authentication (JWT tokens)
- [ ] Implement rate limiting
- [ ] Set up monitoring (CloudWatch/Datadog)
- [ ] Configure CORS properly
- [ ] Use secrets manager for API keys
- [ ] Enable HTTPS/TLS
- [ ] Set up health check endpoints
- [ ] Configure auto-scaling
- [ ] Set up logging aggregation
- [ ] Implement error tracking (Sentry)
- [ ] Add request validation
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline
- [ ] Load test the API
- [ ] Document API endpoints

---

## 📊 Monitoring

### CloudWatch (AWS)

```python
# Add to main.py
import boto3

cloudwatch = boto3.client('cloudwatch')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Send metric to CloudWatch
    cloudwatch.put_metric_data(
        Namespace='RAG-API',
        MetricData=[
            {
                'MetricName': 'RequestDuration',
                'Value': duration * 1000,
                'Unit': 'Milliseconds'
            }
        ]
    )
    
    return response
```

### LangSmith (LangChain Tracing)

```bash
# Add to .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=rag-production
```

No code changes needed - automatic tracing!

---

## 🔧 Environment-Specific Configs

### Development
```python
# config.py
class DevelopmentConfig:
    DEBUG = True
    CHUNK_SIZE = 500  # Smaller for faster reindex
    MAX_SOURCES = 3
    CACHE_ENABLED = False
```

### Staging
```python
class StagingConfig:
    DEBUG = True
    CHUNK_SIZE = 1000
    MAX_SOURCES = 5
    CACHE_ENABLED = True
    CACHE_TTL = 300  # 5 minutes
```

### Production
```python
class ProductionConfig:
    DEBUG = False
    CHUNK_SIZE = 1000
    MAX_SOURCES = 5
    CACHE_ENABLED = True
    CACHE_TTL = 3600  # 1 hour
    RATE_LIMIT = "100/hour"
```

---

## 💰 Cost Optimization

### 1. Cache Embeddings
Already implemented - embeddings are reused

### 2. Use Cheaper LLMs
```python
# Instead of GPT-4 ($0.03/1K tokens)
llm = ChatOpenAI(model_name="gpt-3.5-turbo")  # $0.002/1K tokens

# Or Claude Haiku
llm = ChatAnthropic(model="claude-haiku-20250514")  # $0.00025/1K tokens
```

### 3. Batch Processing
For bulk queries:
```python
# Process multiple queries in parallel
import asyncio

async def batch_query(questions: List[str]):
    tasks = [qa_chain.ainvoke({"question": q}) for q in questions]
    return await asyncio.gather(*tasks)
```

### 4. Use Managed Vector DB Free Tiers
- Pinecone: 1 index free
- Weaviate Cloud: 14-day free trial
- Qdrant: 1GB free cluster

---

## 🆘 Troubleshooting

**Issue: High latency in production**
- Use CDN for static assets
- Enable response compression
- Move to region closer to users
- Increase memory allocation

**Issue: Out of memory errors**
- Reduce batch size
- Use streaming responses
- Increase container memory
- Implement pagination

**Issue: Rate limiting from OpenAI**
- Implement request queuing
- Use exponential backoff
- Cache responses aggressively
- Switch to Azure OpenAI (higher limits)

---

For detailed support, open an issue on GitHub!
