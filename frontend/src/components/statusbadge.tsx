type StatusBadgeProps = {
  status: string;
};

const statusConfig: Record<
  string,
  {
    label: string;
    className: string;
  }
> = {
  queued: {
    label: "대기",
    className: "bg-amber-100 text-amber-700",
  },
  waiting: {
    label: "대기",
    className: "bg-amber-100 text-amber-700",
  },
  대기: {
    label: "대기",
    className: "bg-amber-100 text-amber-700",
  },
  running: {
    label: "분석 중",
    className: "bg-blue-100 text-blue-700",
  },
  processing: {
    label: "분석 중",
    className: "bg-blue-100 text-blue-700",
  },
  "분석 중": {
    label: "분석 중",
    className: "bg-blue-100 text-blue-700",
  },
  completed: {
    label: "완료",
    className: "bg-emerald-100 text-emerald-700",
  },
  finished: {
    label: "완료",
    className: "bg-emerald-100 text-emerald-700",
  },
  완료: {
    label: "완료",
    className: "bg-emerald-100 text-emerald-700",
  },
  failed: {
    label: "실패",
    className: "bg-red-100 text-red-700",
  },
  실패: {
    label: "실패",
    className: "bg-red-100 text-red-700",
  },
};

function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] ?? {
    label: status,
    className: "bg-slate-100 text-slate-700",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${config.className}`}
    >
      {config.label}
    </span>
  );
}

export default StatusBadge;
