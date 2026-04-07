import { ArrowLeft, ArrowRight, Briefcase, Monitor, Package, Sparkles } from "lucide-react";

import { CardSelector } from "@/components/onboarding/inputs/CardSelector";

type StepBusinessTypeProps = {
  value: string | null;
  onChange: (value: string) => void;
  onBack: () => void;
  onContinue: () => void;
};

const options = [
  {
    id: "expertise_services",
    icon: Briefcase,
    title: "Expertise & Services",
    description: "Coaching, consulting, agencies, professionals",
  },
  {
    id: "physical_products",
    icon: Package,
    title: "Physical Products",
    description: "E-commerce, consumer goods, retail",
  },
  {
    id: "software_apps",
    icon: Monitor,
    title: "Software & Apps",
    description: "SaaS, tools, platforms, mobile apps",
  },
  {
    id: "something_else",
    icon: Sparkles,
    title: "Something Else",
    description: "Communities, events, or a bit of everything",
  },
];

export function StepBusinessType({ value, onChange, onBack, onContinue }: StepBusinessTypeProps) {
  const valid = Boolean(value);

  return (
    <div className="animate-fade-up">
      <h1 className="mb-2 text-[24px] font-bold leading-[1.2] tracking-[-0.4px] text-primary sm:text-[28px] sm:tracking-[-0.5px]">
        What best describes your business?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        We&apos;ll use this to match the right frameworks and page structures for you.
      </p>

      <CardSelector options={options} value={value} onChange={onChange} />

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
          type="button"
          disabled={!valid}
          onClick={onContinue}
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
    </div>
  );
}
