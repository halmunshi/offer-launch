import { ArrowLeft, Clock3, Loader2, ShieldCheck, Zap, PencilRuler } from "lucide-react";

import { CardSelector } from "@/components/onboarding/inputs/CardSelector";

import type { FunnelSetupAnswers, SetFunnelAnswer } from "./types";

type StepStyleProps = {
  answers: FunnelSetupAnswers;
  setAnswer: SetFunnelAnswer;
  back: () => void;
  onLaunch: () => void;
  isSubmitting: boolean;
};

const options = [
  {
    id: "high_converting",
    title: "High-Converting Machine",
    titleClassName:
      "mt-1 block text-[17px] leading-[1.05] font-black uppercase tracking-[-0.025em] text-[#1a1a1a] sm:text-[20px] font-[family-name:var(--font-sans)]",
    cardClassName:
      "bg-gradient-to-br from-[#f3f3f3] via-[#dfe2e6] to-[#f9f9f9] border-[#c9ced4] data-[selected=true]:from-[#f5ebe4] data-[selected=true]:via-[#e8e0da] data-[selected=true]:to-[#fff7f2] data-[selected=true]:border-orange",
    descriptionClassName: "text-[#4f5359]",
    description:
      "Bold headlines, urgency elements, punchy direct-response copy. Every pixel drives action. Built to convert - fast.",
    preview: (
      <div className="h-[154px] overflow-hidden rounded-input border border-[#c9ced4] bg-gradient-to-b from-[#f7f7f8] via-[#e6e9ed] to-[#f6f8fa] p-3 text-center sm:h-[168px]">
        <div className="flex items-center justify-center gap-2">
          <Clock3 className="h-3.5 w-3.5 text-[#7b8794]" />
          <div className="h-2 w-18 rounded-full bg-[#8f98a3]" />
        </div>
        <div className="mx-auto mt-3 h-3 w-[86%] rounded bg-[#1a1f26]" />
        <div className="mx-auto mt-2 h-2.5 w-[64%] rounded bg-[#6b7480]" />
        <div className="mx-auto mt-4 w-[86%] rounded-lg border border-[#c8ced6] bg-white/90 p-2.5">
          <div className="h-2.5 w-full rounded bg-[#d7dce3]" />
          <div className="mt-1.5 h-2.5 w-full rounded bg-[#d7dce3]" />
          <div className="mt-2.5 flex h-6 w-full items-center justify-center rounded bg-[#f53c00] text-[10px] font-bold uppercase tracking-wide text-white">
            <Zap className="mr-1 h-3 w-3" />
            Get Instant Access
          </div>
        </div>
        <div className="mx-auto mt-2 h-2 w-[52%] rounded bg-[#9ba3ae]" />
      </div>
    ),
  },
  {
    id: "modern_authority",
    title: "Modern Authority",
    titleClassName:
      "mt-1 block text-[17px] leading-[1.1] font-semibold tracking-[-0.02em] text-[#1f1b17] sm:text-[21px] font-[family-name:var(--font-dm-sans)]",
    cardClassName:
      "bg-gradient-to-br from-[#eaf5ff] via-[#f5faff] to-[#ffffff] border-[#cfe2f5] data-[selected=true]:from-[#e0f1ff] data-[selected=true]:via-[#eef7ff] data-[selected=true]:to-[#ffffff] data-[selected=true]:border-orange",
    descriptionClassName: "text-[#6f6660]",
    description:
      "Clean layout, generous whitespace, confident copy that builds trust. Social proof woven in naturally. The offer speaks for itself.",
    preview: (
      <div className="h-[154px] overflow-hidden rounded-input border border-[#cfe2f5] bg-gradient-to-br from-[#e8f4ff] via-[#f5faff] to-[#ffffff] p-3 text-left sm:h-[168px]">
        <div className="flex items-center justify-between">
          <div className="h-2 w-14 rounded-full bg-[#a6bfd9]" />
          <ShieldCheck className="h-3.5 w-3.5 text-[#4d7399]" />
        </div>
        <div className="mt-4 h-3 w-2/3 rounded bg-[#1f3f5e]" />
        <div className="mt-2 h-2.5 w-3/4 rounded bg-[#88a8c7]" />
        <div className="mt-3 w-[82%] rounded-lg border border-[#cfe2f5] bg-white/92 p-2.5">
          <div className="h-2.5 w-full rounded bg-[#d7e6f5]" />
          <div className="mt-1.5 h-2.5 w-full rounded bg-[#d7e6f5]" />
          <div className="mt-2.5 h-6 w-[70%] rounded bg-[#6f9dc7]" />
        </div>
        <div className="mt-2 h-2 w-1/3 rounded bg-[#bfd4e9]" />
      </div>
    ),
  },
];

export function StepStyle({ answers, setAnswer, back, onLaunch, isSubmitting }: StepStyleProps) {
  const valid = Boolean(answers.funnelStyle);

  function handleSubmit() {
    if (valid && !isSubmitting) {
      onLaunch();
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
        What&apos;s the vibe?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        This sets the look, feel, and voice of your entire funnel.
      </p>

      <CardSelector
        options={options}
        value={answers.funnelStyle || null}
        onChange={(value) => setAnswer("funnelStyle", value)}
      />

      <div className="mx-auto mt-6 flex items-center justify-center gap-3 sm:mt-7">
        <button
          type="button"
          onClick={back}
          className="inline-flex min-h-11 min-w-[138px] items-center justify-center gap-2 rounded-button border-[1.5px] border-border bg-card px-5 py-3 text-sm font-medium text-secondary transition-all hover:-translate-y-px hover:border-[#d4d0cc] hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </button>

        <button
          type="submit"
          disabled={!valid || isSubmitting}
          className={`relative inline-flex min-h-11 min-w-[168px] items-center justify-center gap-2 rounded-button px-6 py-3 text-sm font-semibold text-white transition-all ${
            valid
              ? "bg-orange hover:-translate-y-px hover:bg-[#d63500]"
              : "pointer-events-none translate-y-1 bg-orange opacity-0"
          } ${isSubmitting ? "pointer-events-none" : "pointer-events-auto"}`}
        >
          {isSubmitting ? <Loader2 className="absolute left-3.5 h-4 w-4 animate-spin" /> : null}
          <span>{isSubmitting ? "Launching..." : "Launch Builder"}</span>
          <PencilRuler className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
}
