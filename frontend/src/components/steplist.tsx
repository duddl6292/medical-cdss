type StepListProps = {
  progress: number;
  status?: string;
};

type StepState = "completed" | "current" | "pending" | "failed";

const steps = [
  {
    title: "영상 업로드",
    description: "CT 영상 파일 등록",
  },
  {
    title: "영상 전처리",
    description: "분석에 필요한 영상 정규화",
  },
  {
    title: "AI 모델 분석",
    description: "뇌 CT 병변 영역 분석",
  },
  {
    title: "결과 생성",
    description: "분석 결과 및 시각화 생성",
  },
];

function getCurrentStep(progress: number) {
  if (progress < 20) return 0;
  if (progress < 45) return 1;
  if (progress < 90) return 2;

  return 3;
}

function StepList({ progress, status = "running" }: StepListProps) {
  const currentStep = getCurrentStep(progress);
  const isFailed = status === "failed" || status === "실패";

  const getStepState = (index: number): StepState => {
    if (isFailed && index === currentStep) {
      return "failed";
    }

    if (progress >= 100 || index < currentStep) {
      return "completed";
    }

    if (index === currentStep) {
      return "current";
    }

    return "pending";
  };

  return (
    <ol className="space-y-4">
      {steps.map((step, index) => {
        const stepState = getStepState(index);

        return (
          <li
            key={step.title}
            className="flex items-start gap-4 rounded-xl border border-slate-200 p-4"
          >
            <StepIcon state={stepState} number={index + 1} />

            <div className="flex-1">
              <div className="flex items-center justify-between gap-3">
                <p className="font-semibold text-slate-800">
                  {step.title}
                </p>

                <StepStateText state={stepState} />
              </div>

              <p className="mt-1 text-sm text-slate-500">
                {step.description}
              </p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

type StepIconProps = {
  state: StepState;
  number: number;
};

function StepIcon({ state, number }: StepIconProps) {
  if (state === "completed") {
    return (
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-100 font-bold text-emerald-700">
        ✓
      </span>
    );
  }

  if (state === "current") {
    return (
      <span className="flex h-9 w-9 shrink-0 animate-pulse items-center justify-center rounded-full bg-blue-600 font-bold text-white">
        {number}
      </span>
    );
  }

  if (state === "failed") {
    return (
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-100 font-bold text-red-700">
        !
      </span>
    );
  }

  return (
    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 font-bold text-slate-400">
      {number}
    </span>
  );
}

type StepStateTextProps = {
  state: StepState;
};

function StepStateText({ state }: StepStateTextProps) {
  const stateText: Record<StepState, string> = {
    completed: "완료",
    current: "진행 중",
    pending: "대기",
    failed: "실패",
  };

  const stateColor: Record<StepState, string> = {
    completed: "text-emerald-600",
    current: "text-blue-600",
    pending: "text-slate-400",
    failed: "text-red-600",
  };

  return (
    <span className={`text-xs font-semibold ${stateColor[state]}`}>
      {stateText[state]}
    </span>
  );
}

export default StepList;