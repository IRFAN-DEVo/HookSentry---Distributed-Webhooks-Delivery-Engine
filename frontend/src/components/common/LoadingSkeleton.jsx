import React from 'react';

export function LoadingSkeleton({ className = 'h-4 w-full', count = 1 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`animate-pulse rounded bg-slate-800/60 my-1 ${className}`}
        />
      ))}
    </>
  );
}

export function TableSkeleton({ rows = 5, cols = 5 }) {
  return (
    <div className="w-full space-y-3 p-4">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 items-center">
          {Array.from({ length: cols }).map((_, c) => (
            <div
              key={c}
              className={`h-4 bg-slate-800/60 rounded animate-pulse ${
                c === 0 ? 'w-1/4' : 'flex-1'
              }`}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
