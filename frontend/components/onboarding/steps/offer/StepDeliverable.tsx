import { ArrowLeft, ArrowRight } from "lucide-react";

import { TextArea } from "@/components/onboarding/inputs/TextArea";

type StepDeliverableProps = {
  value: string;
  onChange: (value: string) => void;
  onBack: () => void;
  onContinue: () => void;
};

export function StepDeliverable({ value, onChange, onBack, onContinue }: StepDeliverableProps) {
  const valid = value.trim().length >= 10;

  function handleSubmit() {
    if (valid) {
      onContinue();
    }
  }

  return (
    <form
      className="animate-fade-up"
      onSubmit={(event) => {
        event.preventDefault();
        handleSubmit();
      }}
    >
      <h1 className="mb-2 text-[24px] font-bold leading-[1.2] tracking-[-0.4px] text-primary sm:text-[28px] sm:tracking-[-0.5px]">
        What does the customer actually get?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        List the core deliverables - modules, calls, assets, access, anything they receive.
      </p>

      <TextArea
        placeholder="e.g. 8-week group coaching program with weekly live calls, a private community, and a 60-page workbook..."
        value={value}
        onChange={onChange}
        submitOnEnter
        onEnter={handleSubmit}
      />

      <div className="mx-auto mt-6 flex items-center justify-center gap-3 sm:mt-7">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex min-h-11 min-w-[138px] items-center justify-center gap-2 rounded-button border-[1.5px] border-border bg-card px-5 py-3 text-sm font-medium text-secondary transition-all hover:-translate-y-px hover:border-[#d4d0cc] hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
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
