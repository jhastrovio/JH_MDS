'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, BarChart3, AlertCircle } from 'lucide-react';
import { type DailyMover } from '../types/market-data';

// Fetch real market data and convert to DailyMover format
const fetchRealMoversData = async (): Promise<DailyMover[]> => {
  const symbols = [
    { symbol: 'EUR-USD', category: 'fx' as const },
    { symbol: 'GBP-USD', category: 'fx' as const },
    { symbol: 'USD-JPY', category: 'fx' as const },
    { symbol: 'AUD-USD', category: 'fx' as const },
    { symbol: 'USD-CHF', category: 'fx' as const },
    { symbol: 'USD-CAD', category: 'fx' as const },
    { symbol: 'NZD-USD', category: 'fx' as const },
  ];

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const token = localStorage.getItem('saxo_access_token');
  
  if (!apiBaseUrl || !token) {
    console.warn('Missing API URL or token for movers data');
    return [];
  }

  const movers: DailyMover[] = [];

  for (const { symbol, category } of symbols) {
    try {
      const response = await fetch(`${apiBaseUrl}/market/price/${symbol}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const priceData = await response.json();
        
        // Convert to DailyMover format
        // Note: We don't have historical data for change calculation yet,
        // so we'll use placeholder values until historical data is available
        movers.push({
          symbol,
          price: Number(priceData.price.toFixed(5)),
          change: 0, // Placeholder until we have historical data
          changePercent: 0, // Placeholder until we have historical data
          category,
        });
      }
    } catch (error) {
      console.error(`Error fetching data for ${symbol}:`, error);
    }
  }

  // Sort by symbol for consistent ordering since we don't have real change data yet
  return movers.sort((a, b) => a.symbol.localeCompare(b.symbol));
};

export default function DailyMovers() {
  const [movers, setMovers] = useState<DailyMover[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'fx' | 'rates' | 'indices'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    const loadMoversData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const data = await fetchRealMoversData();
        setMovers(data);
        setLastUpdate(new Date());
        
        if (data.length === 0) {
          setError('No market data available. Check your API connection and authentication.');
        }
      } catch (err) {
        setError('Failed to load market data');
        console.error('Error loading movers data:', err);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadMoversData();
    
    // Update every 30 seconds (less frequent since we don't have real change data yet)
    const interval = setInterval(loadMoversData, 30000);

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
          {lastUpdate && (
            <span className="text-sm text-muted-foreground">
              {lastUpdate.toLocaleTimeString()}
            </span>
          )}
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

      {/* Error State */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <span className="text-sm text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
          <p className="text-muted-foreground">Loading market data...</p>
        </div>
      )}

      {/* Heat Map Grid */}
      {!isLoading && !error && (
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
                    {mover.changePercent === 0 ? 'N/A' : `${mover.changePercent > 0 ? '+' : ''}${mover.changePercent.toFixed(2)}%`}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && filteredMovers.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          <BarChart3 className="mx-auto h-8 w-8 mb-2" />
          <p>No market data available for {selectedCategory} instruments.</p>
          <p className="text-sm mt-1">Check your API connection and authentication.</p>
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-border text-xs text-muted-foreground text-center">
        Real-time data • Updates every 30 seconds
        {movers.length > 0 && (
          <span className="block mt-1">
            Note: Change calculations require historical data (coming soon)
          </span>
        )}
      </div>
    </div>
  );
}