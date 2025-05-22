# Project Todo List

## High Priority (Core Functionality)

### API Implementation
- [x] Create FastAPI router in /api directory
- [x] Implement /api/price endpoint for latest prices
- [ ] Implement /api/ticks endpoint for historical data
- [ ] Implement /api/snapshot endpoint for storage
- [x] Add JWT authentication middleware

### Data Ingestion
- [ ] Complete Saxo WebSocket implementation (partially started in ingest/saxo_ws.py)
- [ ] Add Yahoo Finance WebSocket client for equity indices
- [ ] Add Investing.com polling client for rates
- [ ] Implement fallback data sources
- [ ] Add error handling and reconnection logic

### Frontend (Next.js)
- [ ] Set up Next.js 14 project with app router
- [ ] Create base layout with Tailwind CSS
- [ ] Implement Watchlist component with live updates
- [ ] Implement Daily Movers heat-map component
- [ ] Add v0.dev generated dashboard components
- [ ] Add WebSocket connection management
- [ ] Implement error boundaries

## Medium Priority (Infrastructure & Integration)

### Storage & Caching
- [ ] Complete OneDrive integration (partially started in storage/on_drive.py)
- [ ] Implement Parquet snapshot functionality
- [ ] Set up Redis caching patterns for all data types
- [ ] Add cache invalidation logic
- [ ] Implement backup storage strategy

### Testing & CI/CD
- [x] Add API integration tests
- [ ] Set up GitHub Actions workflow
- [ ] Add frontend component tests
- [ ] Set up Vercel deployment pipeline
- [ ] Add performance benchmarking tests

### Security & Environment
- [ ] Complete environment variables setup
- [ ] Implement secret rotation mechanism
- [ ] Add rate limiting
- [ ] Set up CORS policies
- [ ] Implement API key validation
- [ ] Add request validation middleware

## Lower Priority (Enhancement & Polish)

### Observability
- [ ] Add Sentry integration
- [ ] Set up Vercel Analytics
- [ ] Implement Redis heartbeat monitoring
- [ ] Add basic logging
- [ ] Set up performance monitoring

### Export Features
- [ ] Add CSV export functionality
- [ ] Implement webhook notifications
- [ ] Add email alert system
- [ ] Add Excel export option
- [ ] Implement scheduled exports

### Documentation
- [ ] Complete API documentation
- [ ] Add deployment guide
- [ ] Create user guide
- [ ] Document environment setup
- [ ] Add architecture diagrams
- [ ] Create troubleshooting guide

## Current Progress
✅ Basic project structure set up
✅ Dependencies defined in requirements.txt
✅ Python version requirement set (3.12)
✅ Initial Redis client implementation
✅ Initial Saxo WebSocket client structure
✅ Initial OneDrive storage integration
✅ API contract defined in OpenAPI spec

## Next Steps
1. Implement the /api/ticks and /api/snapshot endpoints
2. Finish the Saxo WebSocket client with error handling
3. Set up the Next.js frontend project
4. Implement the core Watchlist component
