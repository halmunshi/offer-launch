import { ArrowLeft, ArrowRight, CreditCard, Crown, Gem, Tag } from "lucide-react";

import { CardSelector } from "@/components/onboarding/inputs/CardSelector";

type StepPricePointProps = {
  value: string | null;
  onChange: (value: string) => void;
  onBack: () => void;
  onContinue: () => void;
};

const priceOptions = [
  {
    id: "under_100",
    icon: Tag,
    title: "Under $100",
    description: "Low-ticket",
  },
  {
    id: "101_1000",
    icon: CreditCard,
    title: "$101 - $1,000",
    description: "Mid-ticket",
  },
  {
    id: "1001_5000",
    icon: Gem,
    title: "$1,001 - $5,000",
    description: "High-ticket",
  },
  {
    id: "5000_plus",
    icon: Crown,
    title: "$5,000+",
    description: "Premium",
  },
];

export function StepPricePoint({ value, onChange, onBack, onContinue }: StepPricePointProps) {
  const valid = Boolean(value);

  function handleSelect(nextValue: string) {
    onChange(nextValue);
    window.setTimeout(() => {
      onContinue();
    }, 120);
  }

  return (
    <div className="animate-fade-up">
      <h1 className="mb-1.5 text-[22px] font-bold leading-[1.2] tracking-[-0.4px] text-primary sm:text-[24px]">
        What is your offer priced at?
      </h1>
      <p className="mb-5 text-[15px] leading-relaxed text-muted sm:mb-6 sm:text-sm">
        This shapes how aggressive or consultative the copy needs to be.
      </p>

      <div className="mx-auto w-full max-w-[620px]">
        <CardSelector
          options={priceOptions}
          value={value}
          onChange={handleSelect}
          layout="row"
          density="compact"
        />
      </div>

      <div className="mx-auto mt-5 flex items-center justify-center gap-2.5 sm:mt-6">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex min-h-10 min-w-[124px] items-center justify-center gap-1.5 rounded-button border-[1.5px] border-border bg-card px-4 py-2.5 text-[13px] font-medium text-secondary transition-all hover:-translate-y-px hover:border-[#d4d0cc] hover:text-primary"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </button>

        <button
          type="button"
          onClick={onContinue}
          disabled={!valid}
          className={`inline-flex min-h-10 min-w-[124px] items-center justify-center gap-1.5 rounded-button border-none bg-primary px-6 py-2.5 text-[13px] font-semibold text-page transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            valid
              ? "pointer-events-auto translate-y-0 opacity-100 hover:-translate-y-px hover:bg-black/85"
              : "pointer-events-none translate-y-1 opacity-0"
          }`}
        >
          Continue
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
