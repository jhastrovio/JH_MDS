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

export default function Watchlist() {
  const [watchlistData, setWatchlistData] = useState<MarketData[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'fx' | 'rates' | 'indices'>('all');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Initialize with mock data
  useEffect(() => {
    const allSymbols = [...FX_MAJORS, ...RATES, ...INDICES];
    const mockData = allSymbols.map(generateMockData);
    setWatchlistData(mockData);
  }, []);

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      setWatchlistData(prev => 
        prev.map(item => ({
          ...generateMockData(item.symbol),
          sparklineData: [...(item.sparklineData?.slice(1) || []), item.bid], // Add latest price to sparkline
        }))
      );
    }, 3000); // Update every 3 seconds

    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setWatchlistData(prev => prev.map(item => generateMockData(item.symbol)));
      setIsRefreshing(false);
    }, 1000);
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