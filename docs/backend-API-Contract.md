# API Contract

This document defines the OpenAPI/Swagger contract for our market data API, enabling parallel front-end and back-end development and stubbing CI end-to-end tests.

```yaml
openapi: 3.0.1
info:
  title: JH Market Data API
  version: 1.0.0
  description: API for fetching live market prices, historical ticks, and snapshots.
servers:
  - url: https://api.testing.com
    description: Production server
  - url: https://dev.api.testing.com
    description: Development server

security:
  - BearerAuth: []

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    PriceResponse:
      type: object
      properties:
        symbol:
          type: string
          example: EUR-USD
        price:
          type: number
          format: float
          example: 1.0875
        timestamp:
          type: string
          format: date-time
          example: "2025-05-22T08:15:30Z"
    Tick:
      type: object
      properties:
        symbol:
          type: string
          example: EUR-USD
        bid:
          type: number
          example: 1.0874
        ask:
          type: number
          example: 1.0876
        timestamp:
          type: string
          format: date-time
          example: "2025-05-22T08:15:30Z"
    ErrorResponse:
      type: object
      properties:
        code:
          type: integer
          example: 400
        message:
          type: string
          example: Invalid parameter

paths:
  /api/auth/market/price:
    get:
      summary: Get latest price for a symbol using SaxoBank OAuth token
      parameters:
        - name: symbol
          in: query
          required: true
          schema:
            type: string
            example: EUR-USD
      responses:
        '200':
          description: Successful price fetch
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PriceResponse'
        '401':
          description: Unauthorized - Invalid or missing SaxoBank token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '400':
          description: Bad Request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/auth/price:
    get:
      summary: Get latest price for a symbol using internal JWT token
      parameters:
        - name: symbol
          in: query
          required: true
          schema:
            type: string
            example: EUR-USD
      responses:
        '200':
          description: Successful price fetch
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PriceResponse'
        '401':
          description: Unauthorized - Invalid or missing JWT token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '400':
          description: Bad Request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
  /api/auth/market/ticks:
    get:
      summary: Stream or poll ticks for a symbol using SaxoBank OAuth token
      parameters:
        - name: symbol
          in: query
          required: true
          schema:
            type: string
            example: EUR-USD
        - name: since
          in: query
          required: false
          schema:
            type: string
            format: date-time
            example: "2025-05-22T08:00:00Z"
      responses:
        '200':
          description: List of ticks
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Tick'
        '401':
          description: Unauthorized - Invalid or missing SaxoBank token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/auth/ticks:
    get:
      summary: Stream or poll ticks for a symbol using internal JWT token
      parameters:
        - name: symbol
          in: query
          required: true
          schema:
            type: string
            example: EUR-USD
        - name: since
          in: query
          required: false
          schema:
            type: string
            format: date-time
            example: "2025-05-22T08:00:00Z"
      responses:
        '200':
          description: List of ticks
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Tick'
        '401':
          description: Unauthorized - Invalid or missing JWT token
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/auth/snapshot:
    post:
      summary: Trigger snapshot write to storage
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                symbols:
                  type: array
                  items:
                    type: string
                  example: ["EUR-USD", "USD-JPY"]
      responses:
        '202':
          description: Snapshot scheduled
        '500':
          description: Internal Server Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
```

**Auth Headers**

All endpoints require the following HTTP header:

```
Authorization: Bearer <JWT_TOKEN>
```

**Sample cURL**

```bash
# Using SaxoBank OAuth token for market data
curl -H "Authorization: Bearer SAXO_OAUTH_TOKEN" \
     "https://jh-mds-backend.vercel.app/api/auth/market/price?symbol=EUR-USD"

# Using internal JWT token for cached data  
curl -H "Authorization: Bearer JWT_TOKEN" \
     "https://jh-mds-backend.vercel.app/api/auth/price?symbol=EUR-USD"
```

**Sample JSON Response**

```json
{
  "symbol": "EUR-USD",
  "price": 1.0875,
  "timestamp": "2025-05-22T08:15:30Z"
}
```
