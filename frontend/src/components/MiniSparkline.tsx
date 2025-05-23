'use client';

interface MiniSparklineProps {
  data: number[];
  width?: number;
  height?: number;
  strokeWidth?: number;
  className?: string;
}

export default function MiniSparkline({ 
  data, 
  width = 64, 
  height = 32, 
  strokeWidth = 1.5,
  className = ''
}: MiniSparklineProps) {
  if (!data || data.length < 2) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ width, height }}>
        <div className="w-1 h-1 bg-muted-foreground rounded-full" />
      </div>
    );
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1; // Avoid division by zero

  // Create SVG path
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  // Determine color based on trend (first vs last value)
  const trend = data[data.length - 1] - data[0];
  const strokeColor = trend > 0 ? '#16a34a' : trend < 0 ? '#dc2626' : '#6b7280';

  return (
    <div className={className} style={{ width, height }}>
      <svg width={width} height={height} className="overflow-visible">
        <polyline
          points={points}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </div>
  );
} 