// Value Badge component - Green circles for FPS/лв scores
interface ValueBadgeProps {
  value: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ValueBadge({ value, size = 'md', className = '' }: ValueBadgeProps) {
  // Determine color based on value ranges
  const getColorClasses = (val: number) => {
    if (val >= 0.5) return 'bg-green-500/20 text-green-400 border-green-500/30';
    if (val >= 0.3) return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
    if (val >= 0.2) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  };

  const sizeClasses = {
    sm: 'w-10 h-10 text-sm',
    md: 'w-12 h-12 text-base',
    lg: 'w-16 h-16 text-xl',
  };

  return (
    <div
      className={`
        ${sizeClasses[size]}
        ${getColorClasses(value)}
        rounded-full
        border-2
        flex items-center justify-center
        font-bold
        ${className}
      `}
    >
      {Math.round(value * 100)}
    </div>
  );
}
