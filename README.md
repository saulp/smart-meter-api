# Smart Meter API (demo)
# Author: Saul Perdomo 

> Containerized microservice for smart meter data processing - SpryPoint demonstration

## Overview

This API handles smart meter data ingestion, processing, and retrieval for utility management systems. Built as a containerized microservice designed to run on AWS ECS Fargate with auto-scaling capabilities.

## Features

- **RESTful API** for smart meter data operations
- **Containerized** with Docker for consistent deployments  
- **Health checks** for load balancer integration
- **Structured logging** for CloudWatch integration
- **Environment-based configuration** for dev/staging/prod
- **Auto-scaling ready** - stateless design

## API Endpoints

```
GET  /health           - Health check endpoint
GET  /api/meters       - List all meters
GET  /api/meters/:id   - Get specific meter data
POST /api/meters       - Create new meter
PUT  /api/meters/:id   - Update meter data
GET  /api/readings     - Get meter readings
POST /api/readings     - Submit new readings
```

## Local Development

```bash
# clone the repository
git clone https://github.com/saulp/smart-meter-api.git
cd smart-meter-api

# install dependencies
npm install

# start development server
npm run dev

# api available at http://localhost:8080
```

## Docker Usage

```bash
# build the image
docker build -t smart-meter-api .

# run locally
docker run -p 8080:8080 smart-meter-api

# health check
curl http://localhost:8080/health
```

## AWS Deployment

This API is designed to run on AWS ECS Fargate as part of the SpryPoint infrastructure:

- **Container orchestration**: ECS with Fargate
- **Load balancing**: Application Load Balancer with health checks
- **Auto-scaling**: Based on CPU utilization and request count
- **Logging**: CloudWatch logs with structured JSON output
- **Monitoring**: CloudWatch metrics + X-Ray tracing

See the [infrastructure repository](https://github.com/saulp/sprypoint-aws-infrastructure) for complete deployment automation.

## Environment Variables

```bash
NODE_ENV=production          # Environment mode
PORT=8080                   # Server port
DB_HOST=localhost           # Database host
DB_NAME=smart_meters        # Database name
LOG_LEVEL=info             # Logging level
```

## Health Check

The `/health` endpoint provides detailed health information:

```json
{
  "status": "healthy",
  "timestamp": "2025-06-17T10:30:00Z",
  "version": "1.0.0",
  "uptime": 3600,
  "database": "connected"
}
```

## API Examples

### Get Meter Readings
```bash
curl -X GET http://localhost:8080/api/readings \
  -H "Content-Type: application/json"
```

### Submit New Reading
```bash
curl -X POST http://localhost:8080/api/readings \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "SM001",
    "reading": 1234.56,
    "timestamp": "2025-06-17T10:30:00Z"
  }'
```

## Technology Stack

- **Runtime**: Node.js 18+
- **Framework**: Express.js
- **Database**: Compatible with MySQL/PostgreSQL (Aurora)
- **Containerization**: Docker
- **Cloud Platform**: AWS (ECS Fargate)
- **Monitoring**: CloudWatch, X-Ray

## Architecture Integration

This microservice is part of a larger containerized platform:

```
Internet → ALB → ECS Fargate → Smart Meter API → RDS Aurora
                      ↓
                 CloudWatch/X-Ray
```

The API is designed to be:
- **Stateless** for horizontal scaling
- **Cloud-native** with 12-factor app principles
- **Observable** with structured logging and metrics
- **Resilient** with proper error handling and retries

## Development Notes

Built as a demonstration of modern containerized microservice architecture for utility management systems. Focuses on:

- Clean REST API design
- Container-first development
- Cloud-native deployment patterns
- Production-ready observability
- Infrastructure as Code integration

## Production Considerations

- Database connection pooling implemented
- Graceful shutdown handling for container lifecycle
- Request rate limiting and validation
- Security headers and CORS configuration
- Comprehensive error handling and logging

---

*Part of the SpryPoint AWS infrastructure demonstration - see [infrastructure repo](https://github.com/saulp/sprypoint-aws-infrastructure) for complete system architecture.*
