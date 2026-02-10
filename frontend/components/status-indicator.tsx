interface StatusIndicatorProps {
  label: string;
  status: boolean;
}

export function StatusIndicator({ label, status }: StatusIndicatorProps) {
  return (
    <div className="flex items-center gap-2">
      <div
        className={`h-3 w-3 rounded-full ${
          status ? 'bg-cyan-500' : 'bg-red-500'
        } animate-pulse`}
      />
      <span className="text-sm font-medium text-slate-300">
        {label}: <span className={status ? 'text-cyan-400' : 'text-red-400'}>
          {status ? 'OK' : 'FAIL'}
        </span>
      </span>
    </div>
  );
}
