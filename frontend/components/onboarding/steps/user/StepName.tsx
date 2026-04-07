import { ArrowRight } from "lucide-react";

import { TextInput } from "@/components/onboarding/inputs/TextInput";

type StepNameProps = {
  value: string;
  onChange: (value: string) => void;
  onContinue: () => void;
};

export function StepName({ value, onChange, onContinue }: StepNameProps) {
  const valid = value.trim().length >= 2;

  return (
    <form
      className="animate-fade-up"
      onSubmit={(event) => {
        event.preventDefault();
        if (valid) {
          onContinue();
        }
      }}
    >
      <h1 className="mb-2 text-[24px] font-bold leading-[1.2] tracking-[-0.4px] text-primary sm:text-[28px] sm:tracking-[-0.5px]">
        What&apos;s your name?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        We&apos;ll use this to personalize your experience.
      </p>

      <div className="mx-auto max-w-[440px]">
        <TextInput
          autoFocus
          placeholder="Your first name"
          value={value}
          onChange={onChange}
        />
      </div>

      <button
        type="submit"
        disabled={!valid}
        className={`mt-6 inline-flex w-full items-center justify-center gap-2 rounded-button border-none px-8 py-3 text-sm font-semibold transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] sm:mt-7 sm:w-auto ${
          valid
            ? "pointer-events-auto translate-y-0 bg-primary text-page opacity-100 hover:-translate-y-px hover:bg-black/85"
            : "pointer-events-none translate-y-1 bg-primary text-page opacity-0"
        }`}
      >
        Continue
        <ArrowRight className="h-4 w-4" />
      </button>
    </form>
  );
}
