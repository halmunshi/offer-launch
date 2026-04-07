import { ArrowLeft, Loader2 } from "lucide-react";

import { PillSelector } from "@/components/onboarding/inputs/PillSelector";

type StepIndustryProps = {
  selectedIndustry: string | null;
  customIndustry: string;
  onIndustryChange: (value: string) => void;
  onCustomIndustryChange: (value: string) => void;
  onBack: () => void;
  onFinish: () => void;
  isSubmitting: boolean;
};

const industryOptions = [
  { id: "business_entrepreneurship", label: "Business & Entrepreneurship" },
  { id: "marketing_advertising", label: "Marketing & Advertising" },
  { id: "real_estate", label: "Real Estate" },
  { id: "finance_investing", label: "Finance & Investing" },
  { id: "health_fitness", label: "Health & Fitness" },
  { id: "beauty_aesthetics", label: "Beauty & Aesthetics" },
  { id: "relationships_dating", label: "Relationships & Dating" },
  { id: "personal_development", label: "Personal Development" },
  { id: "education_coaching", label: "Education & Coaching" },
  { id: "legal_professional_services", label: "Legal & Professional Services" },
  { id: "ecommerce_retail", label: "E-commerce & Retail" },
  { id: "technology_saas", label: "Technology & SaaS" },
  { id: "local_services", label: "Local Services" },
  { id: "other", label: "Other" },
];

export function StepIndustry({
  selectedIndustry,
  customIndustry,
  onIndustryChange,
  onCustomIndustryChange,
  onBack,
  onFinish,
  isSubmitting,
}: StepIndustryProps) {
  const valid = Boolean(selectedIndustry);

  return (
    <div className="animate-fade-up">
      <h1 className="mb-2 text-[24px] font-bold leading-[1.2] tracking-[-0.4px] text-primary sm:text-[28px] sm:tracking-[-0.5px]">
        What industry are you in?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        This helps our AI write copy that speaks your audience&apos;s language.
      </p>

      <PillSelector
        options={industryOptions}
        value={selectedIndustry}
        onChange={(value) => onIndustryChange(value as string)}
        allowOther
        otherPlaceholder="Type your industry..."
        otherValue={customIndustry}
        onOtherChange={onCustomIndustryChange}
      />

      <div className="mx-auto mt-2 flex items-center justify-center gap-3 sm:mt-1">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex min-h-11 min-w-[138px] items-center justify-center gap-2 rounded-button border-[1.5px] border-border bg-card px-5 py-3 text-sm font-medium text-secondary transition-all hover:-translate-y-px hover:border-[#d4d0cc] hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>

        <button
          type="button"
          disabled={!valid || isSubmitting}
          onClick={onFinish}
          className={`relative inline-flex min-h-11 min-w-[138px] items-center justify-center rounded-button border-none px-8 py-3 text-sm font-semibold text-page transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
            valid || isSubmitting
              ? isSubmitting
                ? "pointer-events-none translate-y-0 bg-primary opacity-100"
                : "pointer-events-auto translate-y-0 bg-primary opacity-100 hover:bg-black/85"
              : "pointer-events-none translate-y-1 bg-primary opacity-0"
          }`}
        >
          {isSubmitting ? <Loader2 className="absolute left-3.5 h-4 w-4 animate-spin" /> : null}
          <span className="text-center">{isSubmitting ? "Saving..." : "Finish"}</span>
        </button>
      </div>
    </div>
  );
}
