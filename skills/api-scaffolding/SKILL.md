---
name: api-scaffolding
description: Production-grade REST and GraphQL API design with FastAPI, Flask, Pydantic data validation, CORS, and JWT authentication.
---

# Production API Scaffolding Skill

## When to Use
Use when building web services, REST endpoints, microservices, or API integrations.

## Guidelines
1. Framework: Prefer FastAPI for high-performance async APIs with automatic OpenAPI/Swagger documentation.
2. Validation: Use Pydantic BaseModel schemas for request body, query params, and response serialization.
3. Status Codes:
   - 200 OK: successful retrieval/update
   - 201 Created: resource created
   - 400 Bad Request: client input validation error
   - 401 Unauthorized: missing or invalid authentication token
   - 404 Not Found: resource does not exist
   - 429 Too Many Requests: rate limited
4. CORS & Middleware: Configure CORS explicitly; avoid wildcard origins in production environments.
