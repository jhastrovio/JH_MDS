# JH Market Data Service - Frontend

A modern, responsive dashboard for live FX, rates, and equity indices market data built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

🎯 **Core Components**
- **Live Watchlist**: Real-time price table with color-coded changes and mini sparklines
- **Daily Movers Heat-map**: Visual grid showing biggest market moves by category
- **Connection Status**: Real-time WebSocket connection monitoring
- **Responsive Design**: Mobile-first design with Tailwind CSS

📊 **Market Coverage**
- **FX Majors**: EUR-USD, GBP-USD, USD-JPY, AUD-USD, USD-CHF, USD-CAD, NZD-USD
- **Government Rates**: UST 2Y/10Y/30Y, Bund 10Y, Gilt 10Y, JGB 10Y
- **Equity Indices**: S&P 500, Nasdaq, DAX, FTSE, Nikkei, HSI

⚡ **Real-time Features**
- Live price updates every 3 seconds
- WebSocket connection management
- Auto-refresh with connection retry logic
- Visual indicators for price movements

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom design system
- **Icons**: Lucide React
- **Charts**: Recharts + Custom SVG sparklines
- **State Management**: React hooks (useState, useEffect)
- **Data Fetching**: Fetch API with backend integration

## Getting Started

### Prerequisites

- Node.js ≥18.0.0
- npm or yarn
- Running backend API (see parent directory)

### Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.local.example .env.local
   ```
   
   Edit `.env.local`:
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open browser**: http://localhost:3000

### Building for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── globals.css         # Global styles
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Dashboard page
│   ├── components/             # React components
│   │   ├── Watchlist.tsx       # Live price table
│   │   ├── DailyMovers.tsx     # Heat-map grid
│   │   ├── ConnectionStatus.tsx # Connection indicator
│   │   └── MiniSparkline.tsx   # SVG sparklines
│   └── types/                  # TypeScript definitions
│       └── market-data.ts      # Market data types
├── package.json
├── tailwind.config.ts          # Tailwind configuration
├── tsconfig.json              # TypeScript configuration
└── next.config.js             # Next.js configuration
```

## Component Architecture

### Dashboard Layout
- **Header**: Branding, connection status, market summary
- **Overview Cards**: Market status, symbol count, latency metrics  
- **Main Grid**: Watchlist (2 cols) + Daily Movers (1 col)
- **Footer**: Coming soon features placeholder

### Watchlist Component
- **Live Data Table**: Symbol, Bid/Ask, Change, High/Low, Trend
- **Category Filtering**: All, FX, Rates, Indices
- **Auto-refresh**: Updates every 3 seconds
- **Visual Indicators**: Color-coded price changes
- **Mini Sparklines**: 20-point price trend charts

### Daily Movers Component  
- **Heat-map Grid**: 2x4 grid of biggest movers
- **Intensity Mapping**: Background color based on move magnitude
- **Category Icons**: Visual categorization (💱📈📊)
- **Real-time Updates**: Refreshes every 5 seconds

### Connection Status
- **Visual Indicators**: Connected (green), Disconnected (red), Reconnecting (orange)
- **Status Text**: Connected/Disconnected/Reconnecting
- **Last Update Time**: Relative timestamp

## Styling & Design System

### Color Palette
- **Bull/Positive**: `#16a34a` (green-600)
- **Bear/Negative**: `#dc2626` (red-600)  
- **Neutral**: `#6b7280` (gray-500)
- **Primary**: Custom HSL variables
- **Background**: Adaptive light/dark mode support

### Typography
- **Primary Font**: Inter (clean, readable)
- **Monospace Font**: Roboto Mono (financial data)
- **Size Scale**: Tailwind's type scale

### Component Classes
```css
.market-card          /* Card container with border & shadow */
.price-positive       /* Green text for positive changes */
.price-negative       /* Red text for negative changes */
.data-table          /* Styled table for financial data */
.sparkline-container /* Container for mini charts */
```

## Data Flow

1. **Mock Data Generation**: Components generate realistic mock data
2. **State Management**: React hooks for component state
3. **Auto-refresh**: setInterval for live updates simulation
4. **Backend Integration**: Prepared for WebSocket/REST API integration

## Deployment

### Vercel (Recommended)

1. **Connect Repository**: Link GitHub repo to Vercel
2. **Environment Variables**: Set `NEXT_PUBLIC_API_BASE_URL` in Vercel dashboard
3. **Deploy**: Automatic deployment on git push

### Manual Deployment

```bash
npm run build
npm start
```

## Backend Integration

The frontend is designed to work with the FastAPI backend:

- **API Endpoints**: `/api/price`, `/api/ticks`, `/api/snapshot`
- **WebSocket**: Real-time price updates (to be implemented)
- **Authentication**: JWT token support (headers configured)

## Future Enhancements

🔮 **Planned Features**
- [ ] Real WebSocket integration with backend
- [ ] Advanced charting with Recharts
- [ ] Alert system with notifications  
- [ ] CSV export functionality
- [ ] Dark/light mode toggle
- [ ] Mobile-optimized PWA
- [ ] Performance monitoring dashboard

## Development

### Adding New Components

1. Create component in `src/components/`
2. Add TypeScript interface in `src/types/`
3. Import and use in `src/app/page.tsx`
4. Update this README

### Styling Guidelines

- Use Tailwind utility classes
- Follow component class naming (`.market-card`, `.price-positive`)
- Maintain color consistency (bull/bear/neutral)
- Ensure responsive design (mobile-first)

## License

This project is part of the JH Market Data Service. See parent directory for license information.

---

**Built with ❤️ for traders and market data enthusiasts** 