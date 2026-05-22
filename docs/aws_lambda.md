# AWS Lambda Best Practices

## Optimizing Cold Starts

Cold starts occur when AWS Lambda creates a new execution environment. Here are proven strategies:

### Provisioned Concurrency
- Keeps functions initialized and ready to respond in double-digit milliseconds
- Costs more but eliminates cold starts entirely
- Best for latency-sensitive applications

### SnapStart for Java
- Reduces cold start times by up to 10x for Java functions
- Creates a snapshot after initialization phase
- Restore from snapshot on subsequent invocations

### Memory Allocation
- Higher memory allocation = more CPU power
- Sweet spot often between 1024MB - 3008MB
- Monitor CloudWatch metrics to find optimal setting

### VPC Considerations
- VPC-attached Lambdas have longer cold starts
- Use Hyperplane ENIs (post-2019) for better performance
- Consider Lambda in public subnet with security groups

### Package Size Optimization
- Minimize deployment package size
- Use Lambda Layers for dependencies
- Remove unused dependencies and code

## Performance Tuning

### Connection Pooling
Keep database connections warm:
```python
# Initialize outside handler
import psycopg2
connection = psycopg2.connect(DATABASE_URL)

def lambda_handler(event, context):
    cursor = connection.cursor()
    # Use connection
```

### Concurrent Execution
- Default limit: 1000 concurrent executions per region
- Request limit increase for high-traffic applications
- Monitor throttling in CloudWatch

### Timeout Configuration
- Set appropriate timeout (default: 3 seconds, max: 15 minutes)
- Longer timeouts don't impact cost directly
- Monitor p99 latencies to set realistic timeouts

## Error Handling

### Retry Behavior
- Asynchronous invocations: 2 automatic retries
- Synchronous invocations: No automatic retries
- Use Dead Letter Queues (DLQ) for failed events

### CloudWatch Logs
- All stdout/stderr automatically captured
- Use structured logging (JSON format)
- Set appropriate log retention periods

## Security Best Practices

### IAM Permissions
- Follow principle of least privilege
- Use resource-based policies when possible
- Avoid inline policies, use managed policies

### Environment Variables
- Never store secrets in plain text
- Use AWS Secrets Manager or Parameter Store
- Encrypt environment variables at rest

### VPC Security
- Use private subnets with NAT Gateway
- Implement security groups with minimal ingress
- Use VPC endpoints for AWS service access
