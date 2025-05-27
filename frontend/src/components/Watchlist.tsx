'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react';
import { type MarketData, FX_MAJORS, RATES, INDICES } from '@/types/market-data';
import MiniSparkline from './MiniSparkline';

// Mock data generator for demo purposes
const generateMockData = (symbol: string): MarketData => {
  const basePrice = Math.random() * 2 + 0.5; // Random base between 0.5-2.5
  const bid = basePrice;
  const ask = bid + 0.0002 + Math.random() * 0.0008; // Spread 0.2-1.0 pips
  const change = (Math.random() - 0.5) * 0.02; // ±1% max change
  const changePercent = (change / bid) * 100;
  
  // Generate sparkline data (last 20 points)
  const sparklineData = Array.from({ length: 20 }, (_, i) => 
    bid + (Math.random() - 0.5) * 0.01
  );

  return {
    symbol,
    bid: Number(bid.toFixed(5)),
    ask: Number(ask.toFixed(5)),
    timestamp: new Date().toISOString(),
    change: Number(change.toFixed(5)),
    changePercent: Number(changePercent.toFixed(2)),
    dayHigh: Number((bid + Math.random() * 0.01).toFixed(5)),
    dayLow: Number((bid - Math.random() * 0.01).toFixed(5)),
    sparklineData,
  };
};

// Fetch real data from backend API
const fetchRealData = async (symbol: string): Promise<MarketData | null> => {
  try {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const token = localStorage.getItem('saxo_access_token');
    
    if (!apiBaseUrl || !token) {
      console.warn(`Missing API URL or token for ${symbol}, using mock data`);
      return null;
    }

    const response = await fetch(`${apiBaseUrl}/api/auth/price?symbol=${symbol}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      console.warn(`Failed to fetch real data for ${symbol}:`, response.status, response.statusText);
      return null;
    }

    const priceData = await response.json();
    
    // Convert backend PriceResponse to MarketData format
    // Note: We don't have all fields from the backend, so we'll use the price for both bid/ask
    const mockSparkline = Array.from({ length: 20 }, () => priceData.price + (Math.random() - 0.5) * 0.01);
    
    return {
      symbol: priceData.symbol,
      bid: Number((priceData.price - 0.0001).toFixed(5)), // Simulate bid slightly below price
      ask: Number((priceData.price + 0.0001).toFixed(5)), // Simulate ask slightly above price
      timestamp: priceData.timestamp,
      change: 0, // We don't have historical data to calculate change yet
      changePercent: 0, // We don't have historical data to calculate change yet
      dayHigh: Number((priceData.price + Math.random() * 0.01).toFixed(5)),
      dayLow: Number((priceData.price - Math.random() * 0.01).toFixed(5)),
      sparklineData: mockSparkline,
    };
  } catch (error) {
    console.error(`Error fetching real data for ${symbol}:`, error);
    return null;
  }
};

// Symbols to fetch real data for (proof of concept)
const REAL_DATA_SYMBOLS = ['EUR-USD', 'GBP-USD'];

// Generate data for a symbol (real or mock)
const generateDataForSymbol = async (symbol: string): Promise<MarketData> => {
  if (REAL_DATA_SYMBOLS.includes(symbol)) {
    const realData = await fetchRealData(symbol);
    if (realData) {
      return realData;
    }
  }
  // Fallback to mock data
  return generateMockData(symbol);
};

export default function Watchlist() {
  const [watchlistData, setWatchlistData] = useState<MarketData[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'fx' | 'rates' | 'indices'>('all');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Initialize with mock data
  useEffect(() => {
    const loadInitialData = async () => {
      const allSymbols = [...FX_MAJORS, ...RATES, ...INDICES];
      const dataPromises = allSymbols.map(generateDataForSymbol);
      const mockData = await Promise.all(dataPromises);
      setWatchlistData(mockData);
    };
    
    loadInitialData();
  }, []);

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(async () => {
      const allSymbols = [...FX_MAJORS, ...RATES, ...INDICES];
      const dataPromises = allSymbols.map(generateDataForSymbol);
      const updatedData = await Promise.all(dataPromises);
      
      setWatchlistData(prev => 
        updatedData.map((newItem, index) => ({
          ...newItem,
          sparklineData: [...(prev[index]?.sparklineData?.slice(1) || []), newItem.bid], // Add latest price to sparkline
        }))
      );
    }, 3000); // Update every 3 seconds

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const allSymbols = [...FX_MAJORS, ...RATES, ...INDICES];
      const dataPromises = allSymbols.map(generateDataForSymbol);
      const refreshedData = await Promise.all(dataPromises);
      setWatchlistData(refreshedData);
    } finally {
      setIsRefreshing(false);
    }
  };

  const getFilteredData = () => {
    switch (selectedCategory) {
      case 'fx':
        return watchlistData.filter(item => FX_MAJORS.includes(item.symbol));
      case 'rates':
        return watchlistData.filter(item => RATES.includes(item.symbol));
      case 'indices':
        return watchlistData.filter(item => INDICES.includes(item.symbol));
      default:
        return watchlistData;
    }
  };

  const getPriceChangeClass = (changePercent?: number) => {
    if (!changePercent) return 'text-neutral';
    if (changePercent > 0) return 'price-positive';
    if (changePercent < 0) return 'price-negative';
    return 'text-neutral';
  };

  const getPriceChangeIcon = (changePercent?: number) => {
    if (!changePercent) return <Minus className="h-3 w-3" />;
    if (changePercent > 0) return <TrendingUp className="h-3 w-3" />;
    if (changePercent < 0) return <TrendingDown className="h-3 w-3" />;
    return <Minus className="h-3 w-3" />;
  };

  const filteredData = getFilteredData();

  return (
    <div className="market-card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-foreground">Market Watchlist</h2>
        
        <div className="flex items-center space-x-4">
          {/* Category Filter */}
          <div className="flex rounded-lg border border-border p-1">
            {[
              { key: 'all', label: 'All' },
              { key: 'fx', label: 'FX' },
              { key: 'rates', label: 'Rates' },
              { key: 'indices', label: 'Indices' },
            ].map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setSelectedCategory(key as any)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  selectedCategory === key
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-2 px-3 py-2 rounded-md border border-border hover:bg-accent transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span className="text-sm">Refresh</span>
          </button>
        </div>
      </div>

      {/* Watchlist Table */}
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Bid</th>
              <th>Ask</th>
              <th>Change</th>
              <th>Change %</th>
              <th>High</th>
              <th>Low</th>
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
            {filteredData.map((item) => (
              <tr key={item.symbol} className="hover:bg-muted/50 transition-colors">
                <td className="font-medium font-mono">{item.symbol}</td>
                <td className="font-mono">{item.bid}</td>
                <td className="font-mono">{item.ask}</td>
                <td className={`font-mono ${getPriceChangeClass(item.changePercent)}`}>
                  <div className="flex items-center space-x-1">
                    {getPriceChangeIcon(item.changePercent)}
                    <span>{item.change ? (item.change > 0 ? '+' : '') + item.change : '0.00000'}</span>
                  </div>
                </td>
                <td className={`font-mono ${getPriceChangeClass(item.changePercent)}`}>
                  {item.changePercent ? (item.changePercent > 0 ? '+' : '') + item.changePercent.toFixed(2) + '%' : '0.00%'}
                </td>
                <td className="font-mono text-bull">{item.dayHigh}</td>
                <td className="font-mono text-bear">{item.dayLow}</td>
                <td>
                  <div className="sparkline-container">
                    <MiniSparkline data={item.sparklineData || []} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredData.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <p>No data available for {selectedCategory} instruments.</p>
        </div>
      )}
    </div>
  );
} 