import { ArrowRight, Megaphone, PhoneCall, ShoppingCart } from "lucide-react";

import { CardSelector } from "@/components/onboarding/inputs/CardSelector";

import type { FunnelSetupAnswers, SetFunnelAnswer } from "./types";

type StepFunnelTypeProps = {
  answers: FunnelSetupAnswers;
  setAnswer: SetFunnelAnswer;
  next: () => void;
  onBack: () => void;
};

const options = [
  {
    id: "lead_generation",
    icon: Megaphone,
    title: "Lead Generation Funnel",
    description: "Capture leads and nurture them toward your offer.",
  },
  {
    id: "call_funnel",
    icon: PhoneCall,
    title: "Call Funnel",
    description: "Qualify and book calls with a VSL or sales page.",
  },
  {
    id: "direct_sales",
    icon: ShoppingCart,
    title: "Direct Sales Funnel",
    description: "Sell directly with a VSL, checkout, and upsells.",
  },
];

export function StepFunnelType({ answers, setAnswer, next, onBack }: StepFunnelTypeProps) {
  const valid = Boolean(answers.funnelType);

  function handleContinue() {
    if (valid) {
      next();
    }
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
        What kind of funnel do you want to build?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        Pick the structure that fits your offer. You can always adjust in the builder.
      </p>

      <CardSelector
        options={options}
        value={answers.funnelType || null}
        onChange={(value) => {
          setAnswer("funnelType", value);
          if (answers.funnelType !== value) {
            setAnswer("integrations", null);
          }
        }}
        layout="grid-3"
      />

      <p className="mt-4 text-xs leading-relaxed text-muted sm:mt-5 sm:text-[13px]">
        This is your starting structure. You can ask the AI to add, remove, or rearrange pages anytime in
        the builder.
      </p>

      <div className="mx-auto mt-6 flex items-center justify-center gap-3 sm:mt-7">
        <button
          type="button"
          onClick={onBack}
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
