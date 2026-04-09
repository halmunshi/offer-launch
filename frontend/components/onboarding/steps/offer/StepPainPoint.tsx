import { ArrowLeft, ArrowRight } from "lucide-react";

import { TextArea } from "@/components/onboarding/inputs/TextArea";

type StepPainPointProps = {
  value: string;
  onChange: (value: string) => void;
  onBack: () => void;
  onContinue: () => void;
};

export function StepPainPoint({ value, onChange, onBack, onContinue }: StepPainPointProps) {
  const hasContent = value.trim().length > 0;

  function handleSubmit() {
    onContinue();
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
        What is your audience&apos;s biggest pain point?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        What keeps them up at night? What are they desperate to solve?
      </p>

      <TextArea
        placeholder="e.g. They're generating leads but can't close them. They've tried every funnel template out there and nothing converts because the copy doesn't speak to their audience..."
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
          className={`inline-flex min-h-11 min-w-[138px] items-center justify-center gap-2 rounded-button px-8 py-3 text-sm font-semibold transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            hasContent
              ? "border-none bg-primary text-page hover:-translate-y-px hover:bg-black/85"
              : "border-[1.5px] border-border bg-transparent text-primary hover:-translate-y-px hover:bg-card"
          }`}
        >
          {hasContent ? "Continue" : "Skip"}
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
}
