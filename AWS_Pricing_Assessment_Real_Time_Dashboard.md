# AWS Pricing Assessment
## Serverless Real-Time Dashboard Architecture

**Document Version:** 1.0
**Date:** November 13, 2025
**Region:** US East (N. Virginia) - us-east-1
**Assessment Type:** Monthly Cost Estimation

---

## Executive Summary

This document provides a comprehensive pricing assessment for deploying a Serverless Real-Time Dashboard on AWS infrastructure. The architecture leverages six core AWS services to deliver a scalable, highly available solution capable of handling 1,000 concurrent users and 500 requests per second.

**Total Estimated Monthly Cost (T.E.M.C.): $2,105.25 USD**

---

## Architecture Overview

The solution utilizes the following AWS services in a serverless architecture pattern:

1. **AWS Lambda** - Backend compute and API processing
2. **Amazon API Gateway** - WebSocket API (real-time connections) + HTTP API (data clients)
3. **Amazon Kinesis Data Streams** - Real-time data ingestion and streaming
4. **Amazon DynamoDB** - NoSQL database with on-demand capacity
5. **Amazon S3** - Static file hosting for dashboard assets
6. **Amazon CloudFront** - Global content delivery network (CDN)

---

## Usage Parameters & Assumptions

The following parameters were used for cost calculation:

| Parameter | Value | Justification |
|-----------|-------|---------------|
| **Concurrent Users** | 1,000 users | Dashboard users with active real-time connections |
| **Connection Duration** | 8 hours/day | Average user session length |
| **Real-Time Data Clients** | 9 clients | 7 dedicated ports + 2 other polling clients |
| **Peak Request Rate** | 500 RPS | Combined load from all users and clients |
| **Monthly API Requests** | 1 Billion (10⁹) | Based on continuous 500 RPS load pattern |
| **Lambda Configuration** | 512 MB, 100ms | Standard configuration for API processing |
| **Kinesis Shards** | 3 shards | Supports ~3 MB/s throughput (500 RPS @ ~6KB/record) |
| **DynamoDB Storage** | 20 GB | On-Demand mode with 100M reads, 10M writes/month |
| **S3 Storage** | 10 GB | Static dashboard files (HTML, CSS, JS, assets) |
| **CloudFront Transfer** | 200 GB/month | Global data delivery to end users |

---

## Detailed Cost Breakdown

### 1. AWS Lambda

| Component | Usage | Unit Price | Calculation | Monthly Cost |
|-----------|-------|------------|-------------|--------------|
| **Request Charges** | 1,000M requests | $0.20 per 1M requests | (1,000M - 1M free tier) × $0.20/1M | $199.80 |
| **Compute Duration** | 50M GB-seconds | $0.0000166667 per GB-s | 1B req × 0.1s × 0.5GB = 50M GB-s<br>(50M - 400K free) × $0.0000166667 | $826.67 |
| **SUBTOTAL** | | | | **$1,026.47** |

**Notes:**
- Processes all API requests with 512 MB memory allocation
- 100ms average execution time per request
- Free tier: 1M requests + 400K GB-seconds per month applied
- Supports both WebSocket and HTTP API backend processing

---

### 2. Amazon API Gateway - WebSocket API

| Component | Usage | Unit Price | Calculation | Monthly Cost |
|-----------|-------|------------|-------------|--------------|
| **Connection Minutes** | 14.4M minutes | $0.25 per 1M minutes | 1,000 users × 8 hrs × 30 days × 60 min<br>14.4M × $0.25/1M | $3.60 |
| **Messages** | 300M messages | $1.00 per 1M messages | ~30% of total requests via WebSocket<br>300M × $1.00/1M | $300.00 |
| **SUBTOTAL** | | | | **$303.60** |

**Notes:**
- Maintains persistent connections for 1,000 concurrent dashboard users
- WebSocket enables real-time bidirectional communication
- Messages metered in 32 KB increments
- Estimated 30% of total API traffic uses WebSocket protocol

---

### 3. Amazon API Gateway - HTTP API

| Component | Usage | Unit Price | Calculation | Monthly Cost |
|-----------|-------|------------|-------------|--------------|
| **API Calls** | 700M requests | $1.00 per 1M requests | 9 data clients polling endpoints<br>~70% of total requests<br>700M × $1.00/1M | $700.00 |
| **SUBTOTAL** | | | | **$700.00** |

**Notes:**
- Serves 9 real-time data clients (7 dedicated ports + 2 others)
- HTTP API chosen over REST API for 71% cost savings ($1.00 vs $3.50 per million)
- Handles polling-based data retrieval
- Data transfer costs included in CloudFront

---

### 4. Amazon Kinesis Data Streams

| Component | Usage | Unit Price | Calculation | Monthly Cost |
|-----------|-------|------------|-------------|--------------|
| **Shard Hours** | 2,160 shard-hours | $0.015 per shard-hour | 3 shards × 24 hrs × 30 days × $0.015 | $32.40 |
| **PUT Payload Units** | Included | - | Included in provisioned mode | $0.00 |
| **SUBTOTAL** | | | | **$32.40** |

**Notes:**
- Provisioned mode with 3 shards for predictable costs
- Each shard capacity: 1 MB/s write, 2 MB/s read
- Total capacity: 3 MB/s write, 6 MB/s read
- Sufficient for 500 RPS at ~6 KB per record
- 24/7 operation for continuous data streaming

---

### 5. Amazon DynamoDB

| Component | Usage | Unit Price | Calculation | Monthly Cost |
|-----------|-------|------------|-------------|--------------|
| **Data Storage** | 20 GB | $0.25 per GB-month | 20 GB × $0.25 | $5.00 |
| **Read Request Units** | 100M RRUs | $0.25 per 1M RRUs | 100M × $0.25/1M | $25.00 |
| **Write Request Units** | 10M WRUs | $1.25 per 1M WRUs | 10M × $1.25/1M | $12.50 |
| **SUBTOTAL** | | | | **$42.50** |

**Notes:**
- On-Demand capacity mode for automatic scaling
- Stores dashboard state, user sessions, and cached data
- Read-heavy workload pattern (10:1 read-to-write ratio)
- No capacity planning required with on-demand mode
- Standard table class for frequently accessed data

---

### 6. Amazon S3

| Component | Usage | Unit Price | Calculation | Monthly Cost |
|-----------|-------|------------|-------------|--------------|
| **Standard Storage** | 10 GB | $0.023 per GB-month | 10 GB × $0.023 | $0.23 |
| **PUT/GET Requests** | Minimal | Various | Estimated (cached by CloudFront) | $0.05 |
| **SUBTOTAL** | | | | **$0.28** |

**Notes:**
- Hosts static dashboard files (HTML, CSS, JavaScript, images)
- First 50 TB storage tier pricing: $0.023/GB
- Request costs minimal due to CloudFront caching
- Serves as origin for CloudFront CDN
- Highly durable (99.999999999%) and available

---

### 7. Amazon CloudFront

| Component | Usage | Unit Price | Calculation | Monthly Cost |
|-----------|-------|------------|-------------|--------------|
| **Data Transfer Out** | 200 GB | $0.040 per GB (after 1TB) | 200 GB within free tier (1 TB) | $0.00 |
| **HTTP/HTTPS Requests** | ~50M requests | Included in free tier | Covered by Always Free Tier | $0.00 |
| **SUBTOTAL** | | | | **$0.00** |

**Notes:**
- Always Free Tier: 1 TB data transfer + 10M requests per month
- 200 GB well within free allocation
- Global edge network reduces latency for dashboard users
- No charge for data transfer from S3 to CloudFront
- SSL/TLS included at no additional cost

---

## Total Monthly Cost Summary

| Service | Monthly Cost | % of Total |
|---------|--------------|------------|
| AWS Lambda | $1,026.47 | 48.8% |
| API Gateway (HTTP) | $700.00 | 33.2% |
| API Gateway (WebSocket) | $303.60 | 14.4% |
| DynamoDB | $42.50 | 2.0% |
| Kinesis Data Streams | $32.40 | 1.5% |
| Amazon S3 | $0.28 | <0.1% |
| Amazon CloudFront | $0.00 | 0.0% |
| **TOTAL** | **$2,105.25** | **100%** |

---

## Cost Optimization Opportunities

### 1. AWS Lambda Optimization (Potential Savings: $150-$250/month)

**Recommendations:**
- **Graviton2 Processors**: Switch to ARM-based architecture for up to 34% price-performance improvement
- **Execution Time Tuning**: Optimize code to reduce average execution from 100ms to 50-75ms
- **Compute Savings Plans**: Commit to 1-year term for up to 17% discount on compute duration charges
- **Memory Right-Sizing**: Analyze CloudWatch metrics to ensure 512 MB is optimal

**Implementation Priority:** High
**Estimated Savings:** ~$200/month (20% reduction)

---

### 2. API Gateway Cost Reduction (Potential Savings: $200-$400/month)

**Recommendations:**
- **Message Batching**: Aggregate multiple WebSocket messages to reduce message count by 20-30%
- **Caching Strategy**: Enable API Gateway caching (additional cost) to reduce Lambda invocations
- **Request Optimization**: Implement client-side request throttling and deduplication
- **Connection Management**: Implement intelligent connection pooling

**Implementation Priority:** Medium
**Estimated Savings:** ~$300/month (30% reduction in message costs)

---

### 3. DynamoDB Capacity Planning (Potential Savings: $10-$20/month)

**Recommendations:**
- **Provisioned Capacity**: If workload is predictable, switch from On-Demand to Provisioned with auto-scaling
- **DynamoDB Accelerator (DAX)**: For read-heavy patterns (additional cost ~$100/month, but saves Lambda costs)
- **Standard-IA Table Class**: Migrate infrequently accessed data to Standard-Infrequent Access tables
- **Time-to-Live (TTL)**: Automatically expire old session data to reduce storage

**Implementation Priority:** Low
**Estimated Savings:** ~$15/month (35% reduction)

---

### 4. Kinesis Right-Sizing (Potential Savings: $10-$15/month)

**Recommendations:**
- **Shard Monitoring**: Track actual throughput utilization via CloudWatch metrics
- **Dynamic Shard Adjustment**: If average load is under 2 MB/s, reduce to 2 shards
- **On-Demand Mode**: Consider on-demand mode if traffic patterns are highly variable
- **Data Retention**: Adjust retention period from default 24 hours if not required

**Implementation Priority:** Low
**Estimated Savings:** ~$11/month (reducing to 2 shards)

---

### 5. Monitoring & Alerting Setup

**Recommended Cost Monitoring:**
- **AWS Cost Explorer**: Enable hourly granularity for service-level cost tracking
- **CloudWatch Dashboards**: Create unified dashboard for key metrics:
  - Lambda invocation count and duration
  - API Gateway request rates and connection count
  - Kinesis throughput and iterator age
  - DynamoDB consumed capacity units
- **AWS Budgets**: Set budget alerts at $1,800, $2,000, and $2,200 thresholds
- **Cost Anomaly Detection**: Enable ML-based anomaly alerts for unusual spending patterns

**Implementation Priority:** High (Immediate)
**Setup Cost:** Minimal (~$2-5/month for detailed monitoring)

---

## Scaling Impact Analysis

### Scenario 1: Double User Load (2,000 Users)

| Service | Current Cost | New Cost | Delta |
|---------|--------------|----------|-------|
| Lambda | $1,026.47 | $1,439.47 | +$413.00 |
| API Gateway (WebSocket) | $303.60 | $606.60 | +$303.00 |
| API Gateway (HTTP) | $700.00 | $700.00 | $0.00 |
| Kinesis | $32.40 | $43.20 | +$10.80 |
| DynamoDB | $42.50 | $67.50 | +$25.00 |
| **TOTAL** | **$2,105.25** | **$2,857.05** | **+$751.80** |

**Cost per Additional User:** ~$0.75/month

---

### Scenario 2: Double API Request Volume (2B requests/month)

| Service | Current Cost | New Cost | Delta |
|---------|--------------|----------|-------|
| Lambda | $1,026.47 | $1,852.47 | +$826.00 |
| API Gateway (HTTP) | $700.00 | $1,400.00 | +$700.00 |
| API Gateway (WebSocket) | $303.60 | $603.60 | +$300.00 |
| Kinesis | $32.40 | $43.20 | +$10.80 |
| DynamoDB | $42.50 | $80.00 | +$37.50 |
| **TOTAL** | **$2,105.25** | **$3,979.07** | **+$1,873.82** |

**Cost per Additional 100M Requests:** ~$187/month

---

### Scenario 3: CloudFront Exceeds Free Tier (1.5 TB transfer)

| Service | Current Cost | New Cost | Delta |
|---------|--------------|----------|-------|
| CloudFront | $0.00 | $20.00 | +$20.00 |
| **TOTAL** | **$2,105.25** | **$2,125.25** | **+$20.00** |

**CloudFront Pricing:** $0.040/GB after first 1 TB free tier

---

## Regional Pricing Comparison

US East (N. Virginia) selected for optimal cost efficiency:

| Region | Relative Cost | Annual Delta | Notes |
|--------|--------------|--------------|-------|
| **us-east-1 (N. Virginia)** | **Baseline** | **$0** | Lowest pricing, selected region |
| us-east-2 (Ohio) | +2-3% | +$504 - $756 | Slightly higher Lambda costs |
| us-west-2 (Oregon) | +3-5% | +$756 - $1,263 | Higher data transfer costs |
| eu-west-1 (Ireland) | +8-12% | +$2,021 - $3,031 | GDPR compliance, EU customers |
| ap-southeast-1 (Singapore) | +15-20% | +$3,789 - $5,052 | APAC region premium pricing |

**Recommendation:** Remain in US East (N. Virginia) unless compliance or latency requirements dictate otherwise.

---

## Cost Governance & Best Practices

### 1. Tagging Strategy

Implement comprehensive resource tagging:
```
Environment: Production
Project: RealTimeDashboard
CostCenter: Engineering
Application: SeaLevelDashboard
ManagedBy: CloudFormation/Terraform
```

**Benefits:**
- Cost allocation reports by project/department
- Automated resource lifecycle management
- Compliance and audit tracking

---

### 2. AWS Cost Management Tools

| Tool | Purpose | Cost | Implementation |
|------|---------|------|----------------|
| **AWS Cost Explorer** | Historical analysis, forecasting | Free | Enable detailed cost tracking |
| **AWS Budgets** | Spending alerts & notifications | Free (2 budgets) | Set at $1,800, $2,000, $2,200 |
| **Cost Anomaly Detection** | ML-based unusual spend alerts | Free | Enable for all services |
| **AWS Trusted Advisor** | Cost optimization recommendations | Included | Review weekly |
| **CloudWatch Dashboards** | Real-time metrics monitoring | ~$3/month | Create unified dashboard |

---

### 3. Reserved Capacity & Savings Plans

**Not Recommended at Current Scale:**
- Current monthly spend ($2,105) is below typical commitment thresholds
- Architecture requires flexibility for scaling
- Re-evaluate when monthly costs consistently exceed $3,000

**Future Consideration (6-12 months):**
- **Lambda Compute Savings Plan**: If Lambda costs exceed $1,500/month consistently
- **DynamoDB Reserved Capacity**: If switching to provisioned mode
- **1-Year No-Upfront Commitment**: Lowest risk option for cost savings

---

## Risk Assessment & Mitigation

### Cost Overrun Risks

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|------------|--------|---------------------|
| **Traffic Spike** | Medium | High | Implement API throttling, Lambda reserved concurrency |
| **WebSocket Connection Leak** | Low | High | Connection timeout policies, monitoring alerts |
| **DynamoDB Hot Partition** | Low | Medium | Partition key design review, enable auto-scaling |
| **Kinesis Throughput Exceeded** | Low | Medium | CloudWatch alarms on WriteProvisionedThroughputExceeded |
| **CloudFront Cache Miss Rate** | Medium | Low | Optimize TTL settings, cache warming |

---

### Security Cost Implications

**AWS WAF (Optional):** ~$20-50/month
- Protect API Gateway endpoints
- Recommended for production environments
- Prevents DDoS and bot attacks

**AWS Shield Standard:** Included (Free)
- Automatic DDoS protection
- No additional cost

**AWS CloudTrail:** ~$0-5/month
- API activity logging for compliance
- First copy of management events free

**AWS Secrets Manager:** ~$1-2/month
- Secure API key and credential storage
- $0.40 per secret per month

**Estimated Security Add-On:** ~$25-60/month

---

## Deployment & Operational Costs

### One-Time Setup Costs

| Activity | Estimated Cost | Notes |
|----------|---------------|-------|
| **Infrastructure as Code Development** | $0 | Using CloudFormation/Terraform (free) |
| **CI/CD Pipeline Setup** | $0 | Using AWS CodePipeline free tier |
| **Initial Testing & Validation** | $50-100 | Estimated load testing costs |
| **Domain & SSL Certificate** | $12/year | Route 53 hosted zone + ACM certificate (free) |

**Total One-Time Cost:** ~$60-110

---

### Ongoing Operational Costs

| Service | Monthly Cost | Annual Cost |
|---------|--------------|-------------|
| **Route 53 Hosted Zone** | $0.50 | $6.00 |
| **CloudWatch Logs (5 GB)** | $2.50 | $30.00 |
| **CloudWatch Alarms (10)** | $1.00 | $12.00 |
| **AWS Support (Developer)** | $29.00 | $348.00 |
| **Backup & Disaster Recovery** | $5.00 | $60.00 |

**Total Operational Overhead:** ~$38/month ($456/year)

**Combined Monthly Cost:** $2,105.25 (services) + $38 (operations) = **$2,143.25**

---

## Financial Summary

### Annual Cost Projection

| Category | Monthly | Annual |
|----------|---------|--------|
| **AWS Services (Core)** | $2,105.25 | $25,263.00 |
| **Operational Overhead** | $38.00 | $456.00 |
| **Security Enhancements** | $40.00 | $480.00 |
| **Monitoring & Logging** | $10.00 | $120.00 |
| **Contingency (10%)** | $219.33 | $2,632.00 |
| **TOTAL ESTIMATED ANNUAL COST** | **$2,412.58** | **$28,951.00** |

---

### Cost per User Metrics

Based on 1,000 concurrent users:
- **Cost per User per Month:** $2.11
- **Cost per User per Year:** $25.26
- **Cost per User per Day:** $0.07

---

### Break-Even Analysis

At 500 RPS and 1,000 concurrent users:
- **Cost per Request:** $0.000002105
- **Cost per Million Requests:** $2.11
- **Daily Operating Cost:** $70.18

---

## Recommendations & Next Steps

### Immediate Actions (Week 1)

1. **Set Up Cost Monitoring**
   - Enable AWS Cost Explorer with hourly granularity
   - Create AWS Budgets with alerts at $1,800, $2,000, $2,200
   - Configure CloudWatch dashboard with key metrics

2. **Implement Resource Tagging**
   - Apply consistent tagging strategy across all resources
   - Enable cost allocation tags in billing console

3. **Security Baseline**
   - Enable AWS CloudTrail logging
   - Configure AWS Secrets Manager for credentials
   - Review IAM policies and implement least privilege

---

### Short-Term Optimization (Month 1-2)

1. **Lambda Optimization**
   - Analyze CloudWatch metrics for execution time patterns
   - Test Graviton2 processors for price-performance gains
   - Implement function warming to reduce cold starts

2. **API Gateway Tuning**
   - Implement request batching where possible
   - Configure connection timeout policies
   - Enable request/response compression

3. **DynamoDB Optimization**
   - Review partition key design for hot partition prevention
   - Implement TTL for automatic data expiration
   - Analyze read/write patterns for provisioned capacity evaluation

---

### Long-Term Strategy (Month 3-6)

1. **Capacity Planning**
   - Monitor actual vs. estimated usage patterns
   - Right-size Kinesis shard count based on real throughput
   - Evaluate Savings Plans when monthly spend stabilizes

2. **Performance Optimization**
   - Implement caching strategies (ElastiCache consideration)
   - Optimize Lambda memory allocation based on profiling
   - Review and optimize DynamoDB indexes

3. **Cost Review Cadence**
   - Monthly cost review meetings
   - Quarterly optimization initiatives
   - Annual architecture review for cost efficiency

---

## Appendix A: Pricing References

### AWS Official Pricing Pages (Accessed: November 2025)

- **Lambda:** https://aws.amazon.com/lambda/pricing/
- **API Gateway:** https://aws.amazon.com/api-gateway/pricing/
- **Kinesis Data Streams:** https://aws.amazon.com/kinesis/data-streams/pricing/
- **DynamoDB:** https://aws.amazon.com/dynamodb/pricing/
- **S3:** https://aws.amazon.com/s3/pricing/
- **CloudFront:** https://aws.amazon.com/cloudfront/pricing/

---

## Appendix B: Calculation Methodology

### Lambda Cost Calculation
```
Request Cost = (Total Requests - Free Tier) × Price per Million
             = (1,000,000,000 - 1,000,000) × $0.20 / 1,000,000
             = $199.80

Compute Cost = Total GB-seconds × Price per GB-second
GB-seconds   = Requests × Duration(s) × Memory(GB)
             = 1,000,000,000 × 0.1 × 0.5
             = 50,000,000 GB-seconds

Cost         = (50,000,000 - 400,000) × $0.0000166667
             = $826.67

Total Lambda = $199.80 + $826.67 = $1,026.47
```

---

### WebSocket Cost Calculation
```
Connection Minutes = Users × Hours/Day × Days × Minutes/Hour
                   = 1,000 × 8 × 30 × 60
                   = 14,400,000 minutes

Connection Cost = 14,400,000 × $0.25 / 1,000,000 = $3.60

Message Cost = 300,000,000 × $1.00 / 1,000,000 = $300.00

Total WebSocket = $3.60 + $300.00 = $303.60
```

---

### Kinesis Cost Calculation
```
Shard Hours = Shards × Hours/Day × Days
            = 3 × 24 × 30
            = 2,160 shard-hours

Cost = 2,160 × $0.015 = $32.40
```

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **RPS** | Requests Per Second - measure of API traffic volume |
| **GB-second** | Lambda pricing unit: memory (GB) × execution time (seconds) |
| **Shard** | Kinesis throughput unit providing 1 MB/s write, 2 MB/s read capacity |
| **RRU** | Read Request Unit - DynamoDB read capacity measurement |
| **WRU** | Write Request Unit - DynamoDB write capacity measurement |
| **Connection Minute** | API Gateway WebSocket pricing unit for persistent connections |
| **On-Demand** | Pay-per-request pricing model without capacity provisioning |
| **Provisioned** | Pre-allocated capacity with fixed hourly cost |
| **T.E.M.C.** | Total Estimated Monthly Cost |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | November 13, 2025 | AI Cost Assessment Agent | Initial comprehensive pricing assessment |

---

## Contact & Support

For questions regarding this assessment:
- **AWS Account Team:** Contact your designated AWS Solutions Architect
- **AWS Support:** Available via AWS Support Console
- **Pricing Questions:** aws-pricing@amazon.com
- **AWS Calculator:** https://calculator.aws/#/

---

**Disclaimer:** Pricing information is based on AWS published rates as of November 2025 for the US East (N. Virginia) region. Actual costs may vary based on usage patterns, service configurations, and promotional credits. This assessment is an estimate and should be validated with actual deployment monitoring. AWS reserves the right to modify pricing; consult current AWS pricing pages for the most up-to-date information.

---

*End of Document*
