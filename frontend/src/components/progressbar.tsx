type ProgressBarProps = {
  progress: number;
};

function ProgressBar({ progress }: ProgressBarProps) {
  const safeProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">
          전체 진행률
        </span>

        <span className="text-sm font-bold text-blue-600">
          {safeProgress}%
        </span>
      </div>

      <div
        className="h-3 w-full overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={safeProgress}
      >
        <div
          className="h-full rounded-full bg-blue-600 transition-all duration-500"
          style={{ width: `${safeProgress}%` }}
        />
      </div>
    </div>
  );
}

export default ProgressBar;