# Apache Kafka Stream Processing

## Core Concepts

### Topics and Partitions
- Topics are logical channels for data
- Partitions enable parallelism and ordering
- Messages in same partition are ordered
- Key determines partition (hash-based)

### Producers and Consumers
- Producers write to topics
- Consumers read from topics in consumer groups
- Each partition consumed by one consumer in a group
- Enables horizontal scaling

## Stream Processing Patterns

### Exactly-Once Semantics
Kafka Streams supports exactly-once processing:

```java
Properties props = new Properties();
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, 
          StreamsConfig.EXACTLY_ONCE_V2);
```

Key components:
- Transactional producers
- Idempotent writes
- Consumer offsets in transactions

### Stateful Processing
Maintain state across events:

```java
KTable<String, Long> wordCounts = textLines
    .flatMapValues(value -> Arrays.asList(value.toLowerCase().split("\\W+")))
    .groupBy((key, word) -> word)
    .count(Materialized.as("counts-store"));
```

Features:
- RocksDB for local state
- Changelog topics for recovery
- Standby replicas for fault tolerance

### Windowing Operations
Time-based aggregations:

- **Tumbling Windows**: Fixed-size, non-overlapping
- **Hopping Windows**: Fixed-size, overlapping
- **Sliding Windows**: Dynamic size based on events
- **Session Windows**: Activity-based windows

```java
KTable<Windowed<String>, Long> counts = stream
    .groupByKey()
    .windowedBy(TimeWindows.of(Duration.ofMinutes(5)))
    .count();
```

## Performance Optimization

### Partitioning Strategy
- More partitions = higher parallelism
- Consider partition count carefully (overhead increases)
- Default partition count: 1 (not recommended for production)
- Rule of thumb: Start with 3x consumer count

### Consumer Configuration
Critical settings:

```properties
# Fetch size impacts throughput
fetch.min.bytes=1
fetch.max.wait.ms=500

# Processing batch size
max.poll.records=500

# Session timeout
session.timeout.ms=30000

# Enable auto-commit or manual commit
enable.auto.commit=false
```

### Producer Tuning
```properties
# Batching for throughput
batch.size=16384
linger.ms=10

# Compression
compression.type=snappy

# Acks for durability
acks=all

# Idempotence
enable.idempotence=true
```

## Reliability Patterns

### Replication
- Replication factor: minimum 3 for production
- In-Sync Replicas (ISR): replicas caught up with leader
- min.insync.replicas=2 for safety

### Consumer Offset Management
Manual offset control:

```java
consumer.commitSync(); // Synchronous commit
consumer.commitAsync(); // Asynchronous commit

// Manual offset control
TopicPartition partition = new TopicPartition("topic", 0);
OffsetAndMetadata offset = new OffsetAndMetadata(100);
consumer.commitSync(Collections.singletonMap(partition, offset));
```

### Error Handling
Strategies:
1. **Retry**: Transient failures
2. **Skip**: Log and continue
3. **DLQ**: Send to dead letter queue
4. **Stop**: Critical failures

## Monitoring

### Key Metrics
Producer metrics:
- record-send-rate
- record-error-rate
- request-latency-avg

Consumer metrics:
- records-consumed-rate
- fetch-latency-avg
- commit-latency-avg

Broker metrics:
- UnderReplicatedPartitions
- OfflinePartitionsCount
- ActiveControllerCount

### CloudWatch Integration
For AWS MSK:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_alarm(
    AlarmName='KafkaHighLag',
    MetricName='EstimatedMaxTimeLag',
    Namespace='AWS/Kafka',
    Statistic='Maximum',
    Period=300,
    EvaluationPeriods=2,
    Threshold=60000,  # 60 seconds
    ComparisonOperator='GreaterThanThreshold'
)
```

## Security

### Authentication
- SASL/SCRAM for username/password
- SASL/PLAIN for simple auth
- mTLS for certificate-based auth
- AWS IAM for MSK

### Authorization
- ACLs for topic-level permissions
- Principle of least privilege
- Separate service accounts per application

### Encryption
- In-transit: TLS/SSL
- At-rest: Encrypted EBS volumes (MSK)
- Client-side encryption for sensitive data
