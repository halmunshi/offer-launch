import { ArrowLeft, Loader2 } from "lucide-react";

import { TextArea } from "@/components/onboarding/inputs/TextArea";

type StepTransformationProps = {
  value: string;
  onChange: (value: string) => void;
  onBack: () => void;
  onSubmit: () => void;
  isSubmitting: boolean;
};

export function StepTransformation({
  value,
  onChange,
  onBack,
  onSubmit,
  isSubmitting,
}: StepTransformationProps) {
  const hasContent = value.trim().length > 0;

  function handleSubmit() {
    if (!isSubmitting) {
      onSubmit();
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
        What does life look like after they complete your program?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        Paint the picture. This becomes the emotional core of your funnel copy.
      </p>

      <TextArea
        placeholder="e.g. They wake up to sales notifications. Their calendar is full of qualified calls. They finally feel like the expert they are, with a system that sells for them 24/7..."
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
          disabled={isSubmitting}
          className={`relative inline-flex min-h-11 min-w-[138px] items-center justify-center rounded-button px-8 py-3 text-sm font-semibold transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            hasContent
              ? "border-none bg-orange text-white hover:-translate-y-px hover:bg-[#d63500]"
              : "border-[1.5px] border-border bg-transparent text-primary hover:-translate-y-px hover:bg-card"
          } ${isSubmitting ? "pointer-events-none" : "pointer-events-auto"}`}
        >
          {isSubmitting ? <Loader2 className="absolute left-3.5 h-4 w-4 animate-spin" /> : null}
          <span>{isSubmitting ? "Saving..." : hasContent ? "Finish" : "Skip"}</span>
        </button>
      </div>
    </form>
  );
}
