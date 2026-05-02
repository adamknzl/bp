/**
 * @file  Badge.tsx
 * @brief Pill-shaped label used to display thematic categories.
 * @author Adam Kinzel (xkinzea00)
 */

import { type ReactNode } from 'react';

interface BadgeProps {
  children:   ReactNode;
  /** Visual size - sm is used in list cards, md in the detail header. */
  size?:       'sm' | 'md';
  /** Full Tailwind background + text colour string (from getCategoryColor). */
  colorClass?: string;
  className?:  string;
}

const SIZE_CLASSES: Record<NonNullable<BadgeProps['size']>, string> = {
  sm: 'px-2.5 py-1 text-[10px]',
  md: 'px-3 py-1.5 text-xs',
};

export default function Badge({
  children,
  size       = 'md',
  colorClass = 'bg-gray-100 text-gray-700',
  className  = '',
}: BadgeProps) {
  return (
    <span className={`${SIZE_CLASSES[size]} ${colorClass} font-bold rounded-full uppercase tracking-wider ${className}`}>
      {children}
    </span>
  );
}