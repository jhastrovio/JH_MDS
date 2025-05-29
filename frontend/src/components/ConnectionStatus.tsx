'use client';

import { Wifi, WifiOff, RotateCcw } from 'lucide-react';
import type { ConnectionStatus as ConnStatus } from '@/types';

interface ConnectionStatusProps {
  status: ConnStatus;
}

export default function ConnectionStatus({ status }: ConnectionStatusProps) {
  const getStatusIcon = () => {
    if (status.reconnecting) {
      return <RotateCcw className="h-4 w-4 animate-spin text-orange-500" />;
    }
    
    if (status.connected) {
      return <Wifi className="h-4 w-4 text-bull" />;
    }
    
    return <WifiOff className="h-4 w-4 text-bear" />;
  };

  const getStatusText = () => {
    if (status.reconnecting) return 'Reconnecting...';
    if (status.connected) return 'Connected';
    return 'Disconnected';
  };

  const getStatusClass = () => {
    if (status.reconnecting) return 'text-orange-500';
    if (status.connected) return 'text-bull';
    return 'text-bear';
  };

  const formatLastUpdate = () => {
    if (!status.lastUpdated) return '';
    const now = new Date();
    const diff = now.getTime() - status.lastUpdated.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  return (
    <div className="flex items-center space-x-2">
      {getStatusIcon()}
      <div className="hidden sm:flex flex-col">
        <span className={`text-xs font-medium ${getStatusClass()}`}>
          {getStatusText()}
        </span>
        {status.lastUpdated && status.connected && (
          <span className="text-xs text-muted-foreground">
            {formatLastUpdate()}
          </span>
        )}
      </div>
    </div>
  );
}