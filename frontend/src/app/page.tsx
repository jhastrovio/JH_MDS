'use client';

import { useState, useEffect } from 'react';
import { Activity, TrendingUp, TrendingDown, Zap } from 'lucide-react';
import { Watchlist, DailyMovers, ConnectionStatus, SaxoAuth } from '@/components';
import { type MarketSummary, type ConnectionStatus as ConnStatus } from '@/types';

export default function Dashboard() {
  const [connectionStatus, setConnectionStatus] = useState<ConnStatus>({
    connected: false,
    reconnecting: false,
  });

  const [marketSummary, setMarketSummary] = useState<MarketSummary>({
    totalSymbols: 0,
    activeStreams: 0,
    lastUpdate: new Date(),
    dailyMovers: [],
  });

  // Simulate connection for demo purposes
  useEffect(() => {
    const timer = setTimeout(() => {
      setConnectionStatus({
        connected: true,
        lastUpdate: new Date(),
        reconnecting: false,
      });
      
      setMarketSummary(prev => ({
        ...prev,
        totalSymbols: 25,
        activeStreams: 3,
        lastUpdate: new Date(),
      }));
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Activity className="h-6 w-6 text-primary" />
                <h1 className="text-xl font-semibold text-foreground">
                  JH Market Data Service
                </h1>
              </div>
              <div className="hidden md:flex items-center space-x-4 text-sm text-muted-foreground">
                <span>FX • Rates • Indices</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <ConnectionStatus status={connectionStatus} />
              <div className="hidden md:flex items-center space-x-4 text-sm">
                <div className="flex items-center space-x-1">
                  <Zap className="h-4 w-4 text-bull" />
                  <span>{marketSummary.totalSymbols} symbols</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Activity className="h-4 w-4 text-primary" />
                  <span>{marketSummary.activeStreams} streams</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Market Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="market-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Market Status</p>
                  <p className="text-2xl font-semibold text-bull">Active</p>
                </div>
                <TrendingUp className="h-8 w-8 text-bull" />
              </div>
            </div>
            
            <div className="market-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Live Symbols</p>
                  <p className="text-2xl font-semibold">{marketSummary.totalSymbols}</p>
                </div>
                <Activity className="h-8 w-8 text-primary" />
              </div>
            </div>
            
            <div className="market-card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Avg Latency</p>
                  <p className="text-2xl font-semibold text-bull">2.3s</p>
                </div>
                <Zap className="h-8 w-8 text-bull" />
              </div>
            </div>
          </div>

          {/* Dashboard Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* SaxoBank Authentication - Full width */}
            <div className="lg:col-span-3">
              <SaxoAuth />
            </div>
            
            {/* Watchlist - Takes up 2 columns */}
            <div className="lg:col-span-2">
              <Watchlist />
            </div>
            
            {/* Daily Movers - Takes up 1 column */}
            <div className="lg:col-span-1">
              <DailyMovers />
            </div>
          </div>

          {/* Additional Features Placeholder */}
          <div className="market-card">
            <div className="text-center py-8">
              <TrendingDown className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-medium text-foreground">
                Coming Soon
              </h3>
              <p className="mt-2 text-sm text-muted-foreground">
                Advanced charting, alerts, and export features are in development.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 