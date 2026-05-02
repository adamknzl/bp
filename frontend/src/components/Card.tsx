/**
 * @file  Card.tsx
 * @brief White rounded container used as the visual base for sidebar panels,
 *        organization cards, and the contact info panel.
 * @author Adam Kinzel (xkinzea00)
 */

import { type ReactNode } from 'react';

interface CardProps {
  children:   ReactNode;
  /** When true, adds a hover shadow transition. */
  hoverable?: boolean;
  padding?:   'sm' | 'md' | 'lg';
  /** Additional Tailwind classes appended to the root element. */
  className?: string;
}

const PADDING_CLASSES: Record<NonNullable<CardProps['padding']>, string> = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export default function Card({
  children,
  hoverable = false,
  padding   = 'md',
  className = '',
}: CardProps) {
  const hoverClasses = hoverable ? 'hover:shadow-md transition-shadow' : '';

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-100 ${PADDING_CLASSES[padding]} ${hoverClasses} ${className}`}>
      {children}
    </div>
  );
}