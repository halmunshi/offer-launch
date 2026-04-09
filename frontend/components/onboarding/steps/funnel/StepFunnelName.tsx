import { ArrowRight } from "lucide-react";

import { TextInput } from "@/components/onboarding/inputs/TextInput";

import type { FunnelSetupAnswers, SetFunnelAnswer } from "./types";

type StepFunnelNameProps = {
  answers: FunnelSetupAnswers;
  setAnswer: SetFunnelAnswer;
  next: () => void;
  onBackToFunnels: () => void;
};

export function StepFunnelName({ answers, setAnswer, next, onBackToFunnels }: StepFunnelNameProps) {
  const value = answers.funnelName ?? "";
  const valid = value.trim().length > 1;

  function handleContinue() {
    if (!valid) {
      return;
    }
    setAnswer("funnelName", value.trim());
    next();
  }

  return (
    <form
      className="animate-fade-up"
      onSubmit={(event) => {
        event.preventDefault();
        handleContinue();
      }}
    >
      <h1 className="mb-2 text-[24px] font-bold leading-[1.2] tracking-[-0.4px] text-primary sm:text-[28px] sm:tracking-[-0.5px]">
        Name your funnel
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        Give it a clear internal name so you can spot it quickly in your funnel list.
      </p>

      <div className="mx-auto max-w-[620px]">
        <TextInput
          label="Funnel name"
          placeholder="e.g. 90-Day Transformation Call Funnel"
          value={value}
          onChange={(nextValue) => setAnswer("funnelName", nextValue)}
          autoFocus
        />
      </div>

      <div className="mx-auto mt-6 flex items-center justify-center gap-3 sm:mt-7">
        <button
          type="button"
          onClick={onBackToFunnels}
          className="inline-flex min-h-11 min-w-[138px] items-center justify-center rounded-button border-[1.5px] border-border bg-card px-5 py-3 text-sm font-medium text-secondary transition-all hover:-translate-y-px hover:border-[#d4d0cc] hover:text-primary"
        >
          Back
        </button>

        <button
          type="submit"
          disabled={!valid}
          className={`inline-flex min-h-11 min-w-[138px] items-center justify-center gap-2 rounded-button border-none bg-primary px-8 py-3 text-sm font-semibold text-page transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            valid
              ? "pointer-events-auto translate-y-0 opacity-100 hover:-translate-y-px hover:bg-black/85"
              : "pointer-events-none translate-y-1 opacity-0"
          }`}
        >
          Continue
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
}
