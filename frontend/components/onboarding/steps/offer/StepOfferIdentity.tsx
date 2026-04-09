import { ArrowRight } from "lucide-react";

import { TextInput } from "@/components/onboarding/inputs/TextInput";

type StepOfferIdentityProps = {
  brandName: string;
  offerName: string;
  offerOneLiner: string;
  onBrandNameChange: (value: string) => void;
  onOfferNameChange: (value: string) => void;
  onOfferOneLinerChange: (value: string) => void;
  onContinue: () => void;
};

export function StepOfferIdentity({
  brandName,
  offerName,
  offerOneLiner,
  onBrandNameChange,
  onOfferNameChange,
  onOfferOneLinerChange,
  onContinue,
}: StepOfferIdentityProps) {
  const valid =
    brandName.trim().length >= 2 && offerName.trim().length >= 2 && offerOneLiner.trim().length >= 10;

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
        What&apos;s your offer?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        Give it a name and a one-liner that tells people exactly what it does.
      </p>

      <div className="mx-auto max-w-[500px] space-y-3 text-left">
        <TextInput
          placeholder="e.g. Apex Marketing Co."
          value={brandName}
          onChange={onBrandNameChange}
          label="Brand or business name"
        />
        <TextInput
          placeholder="e.g. The Conversion Code"
          value={offerName}
          onChange={onOfferNameChange}
          label="Offer name"
        />
        <TextInput
          placeholder="e.g. Turn cold traffic into booked calls in 7 days"
          value={offerOneLiner}
          onChange={onOfferOneLinerChange}
          label="One-liner"
        />
        <p className="pt-0.5 text-xs leading-relaxed text-muted">
          Write a single, punchy sentence that promises a specific outcome in a specific timeframe - make
          it impossible to ignore.
        </p>
      </div>

      <button
        type="submit"
        disabled={!valid}
        className={`mt-6 inline-flex min-h-11 min-w-[138px] items-center justify-center gap-2 rounded-button border-none bg-primary px-8 py-3 text-sm font-semibold text-page transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] sm:mt-7 ${
          valid
            ? "pointer-events-auto translate-y-0 opacity-100 hover:-translate-y-px hover:bg-black/85"
            : "pointer-events-none translate-y-1 opacity-0"
        }`}
      >
        Continue
        <ArrowRight className="h-4 w-4" />
      </button>
    </form>
  );
}
