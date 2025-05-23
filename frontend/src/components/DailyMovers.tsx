'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import { type DailyMover } from '@/types/market-data';

// Mock data generator for daily movers
const generateMockMovers = (): DailyMover[] => {
  const symbols = [
    { symbol: 'EUR-USD', category: 'fx' as const },
    { symbol: 'GBP-USD', category: 'fx' as const },
    { symbol: 'USD-JPY', category: 'fx' as const },
    { symbol: 'SPX', category: 'indices' as const },
    { symbol: 'NDX', category: 'indices' as const },
    { symbol: 'UST-10Y', category: 'rates' as const },
    { symbol: 'BUND-10Y', category: 'rates' as const },
    { symbol: 'DAX', category: 'indices' as const },
  ];

  return symbols.map(({ symbol, category }) => {
    const price = Math.random() * 1000 + 100;
    const changePercent = (Math.random() - 0.5) * 8; // ±4% max
    const change = (price * changePercent) / 100;

    return {
      symbol,
      price: Number(price.toFixed(2)),
      change: Number(change.toFixed(2)),
      changePercent: Number(changePercent.toFixed(2)),
      category,
    };
  }).sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent)); // Sort by magnitude
};

export default function DailyMovers() {
  const [movers, setMovers] = useState<DailyMover[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'fx' | 'rates' | 'indices'>('all');

  useEffect(() => {
    setMovers(generateMockMovers());
    
    // Update every 5 seconds
    const interval = setInterval(() => {
      setMovers(generateMockMovers());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getFilteredMovers = () => {
    const filtered = selectedCategory === 'all' 
      ? movers 
      : movers.filter(mover => mover.category === selectedCategory);
    
    return filtered.slice(0, 8); // Show top 8
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'fx': return '💱';
      case 'rates': return '📈';
      case 'indices': return '📊';
      default: return '📈';
    }
  };

  const getIntensityClass = (changePercent: number) => {
    const abs = Math.abs(changePercent);
    if (abs >= 3) return changePercent > 0 ? 'bg-bull/20 border-bull/40' : 'bg-bear/20 border-bear/40';
    if (abs >= 2) return changePercent > 0 ? 'bg-bull/15 border-bull/30' : 'bg-bear/15 border-bear/30';
    if (abs >= 1) return changePercent > 0 ? 'bg-bull/10 border-bull/20' : 'bg-bear/10 border-bear/20';
    return 'bg-muted/50 border-border';
  };

  const filteredMovers = getFilteredMovers();

  return (
    <div className="market-card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold text-foreground">Daily Movers</h2>
        </div>
        
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
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                selectedCategory === key
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Heat Map Grid */}
      <div className="grid grid-cols-2 gap-3">
        {filteredMovers.map((mover) => (
          <div
            key={mover.symbol}
            className={`
              rounded-lg border p-4 transition-all duration-200 hover:scale-105
              ${getIntensityClass(mover.changePercent)}
            `}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className="text-lg">{getCategoryIcon(mover.category)}</span>
                <span className="font-medium font-mono text-sm">{mover.symbol}</span>
              </div>
              <div className={`
                flex items-center space-x-1 text-xs
                ${mover.changePercent > 0 ? 'text-bull' : mover.changePercent < 0 ? 'text-bear' : 'text-neutral'}
              `}>
                {mover.changePercent > 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : mover.changePercent < 0 ? (
                  <TrendingDown className="h-3 w-3" />
                ) : null}
              </div>
            </div>
            
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-xs text-muted-foreground">Price</span>
                <span className="font-mono text-sm">{mover.price}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-muted-foreground">Change</span>
                <span className={`
                  font-mono text-sm font-medium
                  ${mover.changePercent > 0 ? 'text-bull' : mover.changePercent < 0 ? 'text-bear' : 'text-neutral'}
                `}>
                  {mover.changePercent > 0 ? '+' : ''}{mover.changePercent.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredMovers.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <BarChart3 className="mx-auto h-8 w-8 mb-2" />
          <p>No movers data available</p>
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-border text-xs text-muted-foreground text-center">
        Updates every 5 seconds • Sorted by move magnitude
      </div>
    </div>
  );
} 