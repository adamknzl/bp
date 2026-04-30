import { type ReactNode } from 'react';

interface CardProps {
    children: ReactNode;
    hoverable?: boolean;
    padding: 'sm' | 'md' | 'lg';
    className?: string;
}

export default function Card({
    children,
    hoverable = false,
    padding = 'md',
    className = '',
}: CardProps) {
    const paddingClasses = {
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
    };

    const baseClasses = 'bg-white rounded-xl shadow-sm border border-gray-100';
    const hoverClasses = hoverable ? 'hover:shadow-md transition-shadow' : '';

    return (
        <div className={`${baseClasses} ${paddingClasses[padding]} ${hoverClasses} ${className}`}>
            {children}
        </div>
    );
}