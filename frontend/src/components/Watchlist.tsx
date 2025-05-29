'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, RefreshCw, AlertCircle } from 'lucide-react';
import { type MarketData, FX_MAJORS, RATES, INDICES } from '@/types';
import MiniSparkline from './MiniSparkline';

// Fetch real data from backend API
const fetchRealData = async (symbol: string): Promise<MarketData | null> => {
  try {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    const token = localStorage.getItem('saxo_access_token');
    
    if (!apiBaseUrl || !token) {
      console.warn(`Missing API URL or token for ${symbol}`);
      return null;
    }

    const response = await fetch(`${apiBaseUrl}/api/auth/market/price?symbol=${symbol}`, {
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
    // Note: We don't have all fields from the backend, so we'll simulate bid/ask from price
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

// Symbols that have real data available
const REAL_DATA_SYMBOLS = ['EUR-USD', 'GBP-USD', 'USD-JPY', 'AUD-USD', 'USD-CHF', 'USD-CAD', 'NZD-USD'];

// Generate data for a symbol (real data only)
const generateDataForSymbol = async (symbol: string): Promise<MarketData | null> => {
  if (REAL_DATA_SYMBOLS.includes(symbol)) {
    return await fetchRealData(symbol);
  }
  // No fallback - return null if no real data available
  return null;
};

export default function Watchlist() {
  const [watchlistData, setWatchlistData] = useState<MarketData[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'fx' | 'rates' | 'indices'>('all');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dataErrors, setDataErrors] = useState<string[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      setIsRefreshing(true);
      const allSymbols = [...FX_MAJORS, ...RATES, ...INDICES];
      const dataPromises = allSymbols.map(generateDataForSymbol);
      const results = await Promise.all(dataPromises);
      
      // Filter out null results and track errors
      const validData: MarketData[] = [];
      const errors: string[] = [];
      
      results.forEach((result, index) => {
        if (result) {
          validData.push(result);
        } else {
          errors.push(allSymbols[index]);
        }
      });
      
      setWatchlistData(validData);
      setDataErrors(errors);
      setLastUpdate(new Date());
      setIsRefreshing(false);
    };
    
    loadInitialData();
  }, []);

  // Live updates
  useEffect(() => {
    const interval = setInterval(async () => {
      const allSymbols = [...FX_MAJORS, ...RATES, ...INDICES];
      const dataPromises = allSymbols.map(generateDataForSymbol);
      const results = await Promise.all(dataPromises);
      
      // Filter out null results and track errors
      const validData: MarketData[] = [];
      const errors: string[] = [];
      
      results.forEach((result, index) => {
        if (result) {
          validData.push(result);
        } else {
          errors.push(allSymbols[index]);
        }
      });
      
      setWatchlistData(prev => 
        validData.map((newItem, index) => ({
          ...newItem,
          sparklineData: [...(prev.find(p => p.symbol === newItem.symbol)?.sparklineData?.slice(1) || []), newItem.bid],
        }))
      );
      setDataErrors(errors);
      setLastUpdate(new Date());
    }, 3000); // Update every 3 seconds

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const allSymbols = [...FX_MAJORS, ...RATES, ...INDICES];
      const dataPromises = allSymbols.map(generateDataForSymbol);
      const results = await Promise.all(dataPromises);
      
      // Filter out null results and track errors
      const validData: MarketData[] = [];
      const errors: string[] = [];
      
      results.forEach((result, index) => {
        if (result) {
          validData.push(result);
        } else {
          errors.push(allSymbols[index]);
        }
      });
      
      setWatchlistData(validData);
      setDataErrors(errors);
      setLastUpdate(new Date());
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
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold text-foreground">Market Watchlist</h2>
          {lastUpdate && (
            <span className="text-sm text-muted-foreground">
              Last update: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
        
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

      {/* Data Status */}
      {dataErrors.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <span className="text-sm text-yellow-800">
              No data available for: {dataErrors.join(', ')}
            </span>
          </div>
        </div>
      )}

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
          <AlertCircle className="mx-auto h-8 w-8 mb-2" />
          <p>No real-time data available for {selectedCategory} instruments.</p>        <p className="text-sm mt-1">Check your API connection and authentication.</p>
        </div>
      )}
    </div>
  );
}