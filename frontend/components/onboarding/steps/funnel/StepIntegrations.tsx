import { ArrowLeft, ArrowRight } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

import { TextArea } from "@/components/onboarding/inputs/TextArea";
import { TextInput } from "@/components/onboarding/inputs/TextInput";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

import type {
  CallFunnelIntegrations,
  DirectSalesIntegrations,
  FunnelSetupAnswers,
  LeadMagnetIntegrations,
  SetFunnelAnswer,
} from "./types";

type StepIntegrationsProps = {
  answers: FunnelSetupAnswers;
  setAnswer: SetFunnelAnswer;
  next: () => void;
  back: () => void;
  entryDirection: 1 | -1;
};

const leadMagnetOptions = [
  { id: "pdf_guide", label: "PDF / Guide" },
  { id: "video_training", label: "Video training" },
  { id: "checklist", label: "Checklist" },
  { id: "template_swipe", label: "Template / Swipe file" },
  { id: "other", label: "Other" },
  { id: "later_with_ai", label: "I don't have one yet — help me create it later with AI" },
];

const calendarOptions = [
  { id: "calendly", label: "Calendly" },
  { id: "cal.com", label: "Cal.com" },
  { id: "gohighlevel", label: "GoHighLevel" },
  { id: "hubspot", label: "Hubspot" },
  { id: "other", label: "Other" },
  { id: "none", label: "I don't have one" },
];

const paymentOptions = [
  { id: "stripe", label: "Stripe" },
  { id: "paypal", label: "PayPal" },
  { id: "other", label: "Other" },
  { id: "none", label: "None" },
];

const callStepVariants = {
  enter: (direction: 1 | -1) => ({
    opacity: 0,
    y: direction === 1 ? 22 : -22,
  }),
  center: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
    },
  },
  exit: (direction: 1 | -1) => ({
    opacity: 0,
    y: direction === 1 ? -22 : 22,
    transition: {
      duration: 0.22,
    },
  }),
};

function LeadMagnetVariant({ answers, setAnswer, next, back }: StepIntegrationsProps) {
  const initialIntegrations = (answers.integrations as LeadMagnetIntegrations | null) ?? null;
  const [leadMagnetType, setLeadMagnetType] = useState(initialIntegrations?.leadMagnetType ?? "");
  const [leadMagnetDescription, setLeadMagnetDescription] = useState(
    initialIntegrations?.leadMagnetDescription ?? "",
  );

  const isLater = leadMagnetType === "later_with_ai";
  const hasType = leadMagnetType.length > 0;
  const hasDescription = leadMagnetDescription.trim().length > 0;
  const valid = hasType && (isLater || hasDescription);

  function handleContinue() {
    if (!valid) {
      return;
    }

    setAnswer("integrations", {
      leadMagnetType,
      leadMagnetDescription: leadMagnetDescription.trim(),
      leadMagnetReady: !isLater,
    });
    next();
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
        What will your lead receive after they submit their info?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        This is your lead magnet - what you give in exchange for their details.
      </p>

      <RadioGroup value={leadMagnetType} onValueChange={setLeadMagnetType} className="mx-auto max-w-[620px] gap-2">
        {leadMagnetOptions.map((option) => {
          const selected = leadMagnetType === option.id;
          return (
            <label
              key={option.id}
              className={`flex cursor-pointer items-center gap-2 rounded-input border-[1.5px] px-3 py-2.5 text-left text-sm transition-all duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                selected
                  ? "border-orange bg-selected text-primary shadow-[inset_0_0_0_1px_var(--orange)]"
                  : "border-border bg-card text-primary hover:-translate-y-px hover:border-[#d4d0cc] hover:bg-surface"
              }`}
            >
              <RadioGroupItem value={option.id} />
              <span>{option.label}</span>
            </label>
          );
        })}
      </RadioGroup>

      {!isLater ? (
        <div className="mx-auto mt-4 max-w-[620px]">
          <TextInput
            label="Describe your lead magnet (title or short description)"
            placeholder="e.g. The 7-Step Client Acquisition Checklist"
            value={leadMagnetDescription}
            onChange={setLeadMagnetDescription}
          />
        </div>
      ) : null}

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

function CallFunnelVariant({ answers, setAnswer, next, back, entryDirection }: StepIntegrationsProps) {
  const initialIntegrations = (answers.integrations as CallFunnelIntegrations | null) ?? null;
  const [hasVsl, setHasVsl] = useState<boolean | null>(initialIntegrations?.hasVsl ?? null);
  const [vslEmbed, setVslEmbed] = useState(initialIntegrations?.vslEmbed ?? "");
  const [calendarProvider, setCalendarProvider] = useState(initialIntegrations?.calendarProvider ?? "");
  const [calendarEmbed, setCalendarEmbed] = useState(initialIntegrations?.calendarEmbed ?? "");
  const [showNoCalendarModal, setShowNoCalendarModal] = useState(false);
  const [callStage, setCallStage] = useState<0 | 1>(
    entryDirection === -1 && Boolean(initialIntegrations?.calendarProvider) ? 1 : 0,
  );
  const [callStageDirection, setCallStageDirection] = useState<1 | -1>(1);

  const vslValid = hasVsl !== null;
  const calendarValid = calendarProvider.length > 0;
  const valid = callStage === 0 ? vslValid : calendarValid;

  function handleContinue() {
    if (callStage === 0) {
      if (!vslValid) {
        return;
      }

      setAnswer("integrations", {
        hasVsl: hasVsl === true,
        vslEmbed: vslEmbed.trim(),
        calendarProvider,
        calendarEmbed: calendarEmbed.trim(),
      });
      setCallStageDirection(1);
      setCallStage(1);
      return;
    }

    if (!calendarValid) {
      return;
    }

    setAnswer("integrations", {
      hasVsl: hasVsl === true,
      vslEmbed: vslEmbed.trim(),
      calendarProvider,
      calendarEmbed: calendarEmbed.trim(),
    });
    next();
  }

  return (
    <>
      <form
        className="animate-fade-up"
        onSubmit={(event) => {
          event.preventDefault();
          handleContinue();
        }}
      >
        <div className="mx-auto max-w-[620px] text-left">
          <AnimatePresence mode="wait" custom={callStageDirection}>
            {callStage === 0 ? (
              <motion.div
                key="vsl"
                custom={callStageDirection}
                variants={callStepVariants}
                initial="enter"
                animate="center"
                exit="exit"
              >
                <h1 className="mb-2 text-[24px] font-bold leading-[1.2] tracking-[-0.4px] text-primary sm:text-[28px] sm:tracking-[-0.5px]">
                  Will you use a VSL?
                </h1>
                <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
                  You can add this now or later in the builder.
                </p>

                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setHasVsl(true)}
                      className={`rounded-input border px-3 py-2 text-sm font-medium transition-colors ${
                        hasVsl === true
                          ? "border-orange bg-selected text-primary"
                          : "border-border bg-card text-secondary hover:bg-surface"
                      }`}
                    >
                      Yes
                    </button>
                    <button
                      type="button"
                      onClick={() => setHasVsl(false)}
                      className={`rounded-input border px-3 py-2 text-sm font-medium transition-colors ${
                        hasVsl === false
                          ? "border-orange bg-selected text-primary"
                          : "border-border bg-card text-secondary hover:bg-surface"
                      }`}
                    >
                      No
                    </button>
                  </div>

                  {hasVsl ? (
                    <div>
                      <TextArea
                        label="Paste your VSL embed link here"
                        placeholder="e.g. https://www.loom.com/embed/..."
                        value={vslEmbed}
                        onChange={setVslEmbed}
                        minRows={2}
                      />
                    </div>
                  ) : null}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="calendar"
                custom={callStageDirection}
                variants={callStepVariants}
                initial="enter"
                animate="center"
                exit="exit"
              >
                <h1 className="mb-2 text-[24px] font-bold leading-[1.2] tracking-[-0.4px] text-primary sm:text-[28px] sm:tracking-[-0.5px]">
                  What calendar booking system are you using?
                </h1>
                <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
                  Choose your calendar tool. You can still update embed details later in the builder.
                </p>

                <div className="space-y-4">
                  <RadioGroup
                    value={calendarProvider}
                    onValueChange={(value) => {
                      setCalendarProvider(value);
                      if (value === "none") {
                        setShowNoCalendarModal(true);
                      }
                    }}
                    className="gap-2"
                  >
                    {calendarOptions.map((option) => {
                      const selected = calendarProvider === option.id;
                      return (
                        <label
                          key={option.id}
                          className={`flex cursor-pointer items-center gap-2 rounded-input border-[1.5px] px-3 py-2.5 text-sm transition-all duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                            selected
                              ? "border-orange bg-selected text-primary shadow-[inset_0_0_0_1px_var(--orange)]"
                              : "border-border bg-card text-primary hover:-translate-y-px hover:border-[#d4d0cc] hover:bg-surface"
                          }`}
                        >
                          <RadioGroupItem value={option.id} />
                          <span>{option.label}</span>
                        </label>
                      );
                    })}
                  </RadioGroup>

                  {calendarProvider && calendarProvider !== "none" ? (
                    <div>
                      <TextArea
                        label="Paste your calendar embed link or iframe here"
                        placeholder="e.g. https://cal.com/your-name"
                        value={calendarEmbed}
                        onChange={setCalendarEmbed}
                        minRows={2}
                      />
                    </div>
                  ) : null}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="mx-auto mt-6 flex items-center justify-center gap-3 sm:mt-7">
          <button
            type="button"
            onClick={() => {
              if (callStage === 1) {
                setCallStageDirection(-1);
                setCallStage(0);
                return;
              }
              back();
            }}
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

      <Dialog open={showNoCalendarModal} onOpenChange={setShowNoCalendarModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Calendar setup note</DialogTitle>
            <DialogDescription>
              This is a beta version of this app. We don&apos;t have a calendar-building feature in our AI
              yet. You can integrate with external calendars instead.
            </DialogDescription>
          </DialogHeader>
          <p className="text-sm text-secondary">
            We recommend Cal.com - it&apos;s free and looks great. Set one up and tell the AI in the funnel
            chat, and it will embed it for you.
          </p>
          <div className="mt-5 flex justify-end">
            <button
              type="button"
              onClick={() => setShowNoCalendarModal(false)}
              className="inline-flex h-10 items-center rounded-button bg-primary px-5 text-sm font-semibold text-page transition-colors hover:bg-black/85"
            >
              OK
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function DirectSalesVariant({ answers, setAnswer, next, back }: StepIntegrationsProps) {
  const initialIntegrations = (answers.integrations as DirectSalesIntegrations | null) ?? null;
  const [paymentProcessor, setPaymentProcessor] = useState(initialIntegrations?.paymentProcessor ?? "");

  const valid = paymentProcessor.length > 0;

  function handleContinue() {
    if (!valid) {
      return;
    }

    setAnswer("integrations", {
      paymentProcessor,
      paymentEmbed: "",
    });
    next();
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
        Do you have a payment processor set up?
      </h1>
      <p className="mb-6 text-sm leading-relaxed text-muted sm:mb-7 sm:text-[15px]">
        We&apos;ll need this to connect your checkout page.
      </p>

      <RadioGroup value={paymentProcessor} onValueChange={setPaymentProcessor} className="mx-auto max-w-[620px] gap-2">
        {paymentOptions.map((option) => {
          const selected = paymentProcessor === option.id;
          return (
            <label
              key={option.id}
              className={`flex cursor-pointer items-center gap-2 rounded-input border-[1.5px] px-3 py-2.5 text-sm transition-all duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                selected
                  ? "border-orange bg-selected text-primary shadow-[inset_0_0_0_1px_var(--orange)]"
                  : "border-border bg-card text-primary hover:-translate-y-px hover:border-[#d4d0cc] hover:bg-surface"
              }`}
            >
              <RadioGroupItem value={option.id} />
              <span>{option.label}</span>
            </label>
          );
        })}
      </RadioGroup>

      {paymentProcessor === "none" ? (
        <p className="mx-auto mt-4 max-w-[620px] rounded-input border border-border bg-surface px-3 py-2.5 text-left text-sm text-secondary">
          You&apos;ll need a payment processor before your funnel can go live. We recommend Stripe. Just let
          the funnel AI know in chat.
        </p>
      ) : null}

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

export function StepIntegrations(props: StepIntegrationsProps) {
  if (props.answers.funnelType === "lead_generation") {
    return <LeadMagnetVariant {...props} />;
  }

  if (props.answers.funnelType === "call_funnel") {
    return <CallFunnelVariant {...props} />;
  }

  return <DirectSalesVariant {...props} />;
}
