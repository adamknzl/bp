import { type ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  size?: 'sm' | 'md';
  colorClass?: string;
  className?: string;
}

export default function Badge({
  children,
  size = 'md',
  colorClass = 'bg-gray-100 text-gray-700',
  className = '',
}: BadgeProps) {
  const sizeClasses = {
    sm: 'px-2.5 py-1 text-[10px]',
    md: 'px-3 py-1.5 text-xs',
  };

  return (
    <span
      className={`${sizeClasses[size]} ${colorClass} font-bold rounded-full uppercase tracking-wider ${className}`}
    >
      {children}
    </span>
  );
}