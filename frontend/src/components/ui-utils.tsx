import React, { useEffect, useState } from 'react';

export const RISK_COLORS = {
  Green: '#4C9F70',
  Yellow: '#C9A227',
  Orange: '#C9752D',
  Red: '#B84A3E',
  Purple: '#7A5C9E',
  Default: '#6B7075'
};

export const getRiskColor = (band?: string) => {
  if (!band) return RISK_COLORS.Default;
  return RISK_COLORS[band as keyof typeof RISK_COLORS] || RISK_COLORS.Default;
};

// --- Animated Number Component ---
export function AnimatedNumber({ value, suffix = '', duration = 1000 }: { value: number, suffix?: string, duration?: number }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime: number;
    let animationFrame: number;

    const animate = (time: number) => {
      if (!startTime) startTime = time;
      const progress = Math.min((time - startTime) / duration, 1);
      const easeProgress = 1 - Math.pow(1 - progress, 4);
      setDisplayValue(value * easeProgress);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [value, duration]);

  return <span>{displayValue.toFixed(1)}{suffix}</span>;
}

// --- Radial Gauge Component ---
export function RadialGauge({ 
  value, max = 100, color, size = 60, strokeWidth = 4, children
}: { 
  value: number; max?: number; color: string; size?: number; strokeWidth?: number; children?: React.ReactNode;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const safeValue = isNaN(value) ? 0 : value;
  const strokeDashoffset = circumference - (safeValue / max) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#262B31" strokeWidth={strokeWidth} />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={strokeWidth} strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} className="transition-all duration-1000 ease-out" />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        {children}
      </div>
    </div>
  );
}
