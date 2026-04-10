"use client";

import { useAuth } from "@clerk/nextjs";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { OnboardingShell } from "@/components/onboarding/OnboardingShell";
import { StepDeliverable } from "@/components/onboarding/steps/offer/StepDeliverable";
import { StepIdealClient } from "@/components/onboarding/steps/offer/StepIdealClient";
import { StepOfferIdentity } from "@/components/onboarding/steps/offer/StepOfferIdentity";
import { StepPainPoint } from "@/components/onboarding/steps/offer/StepPainPoint";
import { StepPricePoint } from "@/components/onboarding/steps/offer/StepPricePoint";
import { StepTransformation } from "@/components/onboarding/steps/offer/StepTransformation";
import { useOnboarding } from "@/hooks/useOnboarding";
import { api } from "@/lib/api";

type OfferOnboardingAnswers = {
  brandName: string;
  offerName: string;
  offerOneLiner: string;
  pricePoint: string;
  deliverable: string;
  idealClient: string;
  painPoint: string;
  transformation: string;
};

const stepProgress = [8, 25, 41, 58, 75, 91];

const pricePointLabelById: Record<string, string> = {
  under_100: "Under $100",
  "101_1000": "$101 - $1,000",
  "1001_5000": "$1,001 - $5,000",
  "5000_plus": "$5,000+",
};

const variants = {
  enter: (direction: 1 | -1) => ({
    opacity: 0,
    x: direction === 1 ? 100 : -100,
  }),
  center: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.4,
      ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
    },
  },
  exit: (direction: 1 | -1) => ({
    opacity: 0,
    x: direction === 1 ? -100 : 100,
    transition: {
      duration: 0.3,
    },
  }),
};

export default function NewOfferPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [visualProgress, setVisualProgress] = useState<number | null>(null);

  const onboarding = useOnboarding<OfferOnboardingAnswers>({
    totalSteps: 6,
    initialAnswers: {
      brandName: "",
      offerName: "",
      offerOneLiner: "",
      pricePoint: "",
      deliverable: "",
      idealClient: "",
      painPoint: "",
      transformation: "",
    },
  });

  async function submitOfferIntake() {
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const token = await getToken();

      const payload = {
        name: onboarding.answers.offerName.trim(),
        intake_data: {
          brand_name: onboarding.answers.brandName.trim(),
          offer_name: onboarding.answers.offerName.trim(),
          offer_one_liner: onboarding.answers.offerOneLiner.trim(),
          price_point:
            pricePointLabelById[onboarding.answers.pricePoint] ?? onboarding.answers.pricePoint,
          whats_included: onboarding.answers.deliverable.trim(),
          transformation: onboarding.answers.transformation.trim(),
          ideal_client: onboarding.answers.idealClient.trim(),
          pain_point: onboarding.answers.painPoint.trim(),
        },
      };

      const response = await api.post<{ id: string }, typeof payload>("/offers", payload, token);
      setVisualProgress(100);
      window.setTimeout(() => {
        router.push(`/offers/${response.id}`);
      }, 260);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Unable to create offer.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <OnboardingShell
      progress={visualProgress ?? stepProgress[onboarding.currentStep] ?? 0}
      activeDot={onboarding.currentStep}
      totalDots={6}
      showLogo={false}
      visualVariant="offer"
      onExit={() => router.push("/offers")}
      exitLabel="Exit setup"
    >
      <div className="min-h-[520px] sm:min-h-[440px]">
        <AnimatePresence mode="wait" custom={onboarding.direction}>
          <motion.div
            key={onboarding.currentStep}
            custom={onboarding.direction}
            variants={variants}
            initial="enter"
            animate="center"
            exit="exit"
          >
            {onboarding.currentStep === 0 ? (
              <StepOfferIdentity
                brandName={onboarding.answers.brandName}
                offerName={onboarding.answers.offerName}
                offerOneLiner={onboarding.answers.offerOneLiner}
                onBrandNameChange={(value) => onboarding.setAnswer("brandName", value)}
                onOfferNameChange={(value) => onboarding.setAnswer("offerName", value)}
                onOfferOneLinerChange={(value) => onboarding.setAnswer("offerOneLiner", value)}
                onContinue={onboarding.next}
              />
            ) : null}

            {onboarding.currentStep === 1 ? (
              <StepPricePoint
                value={onboarding.answers.pricePoint || null}
                onChange={(value) => onboarding.setAnswer("pricePoint", value)}
                onBack={onboarding.back}
                onContinue={onboarding.next}
              />
            ) : null}

            {onboarding.currentStep === 2 ? (
              <StepDeliverable
                value={onboarding.answers.deliverable}
                onChange={(value) => onboarding.setAnswer("deliverable", value)}
                onBack={onboarding.back}
                onContinue={onboarding.next}
              />
            ) : null}

            {onboarding.currentStep === 3 ? (
              <StepIdealClient
                value={onboarding.answers.idealClient}
                onChange={(value) => onboarding.setAnswer("idealClient", value)}
                onBack={onboarding.back}
                onContinue={onboarding.next}
              />
            ) : null}

            {onboarding.currentStep === 4 ? (
              <StepPainPoint
                value={onboarding.answers.painPoint}
                onChange={(value) => onboarding.setAnswer("painPoint", value)}
                onBack={onboarding.back}
                onContinue={onboarding.next}
              />
            ) : null}

            {onboarding.currentStep === 5 ? (
              <StepTransformation
                value={onboarding.answers.transformation}
                onChange={(value) => onboarding.setAnswer("transformation", value)}
                onBack={onboarding.back}
                onSubmit={submitOfferIntake}
                isSubmitting={isSubmitting}
              />
            ) : null}
          </motion.div>
        </AnimatePresence>

        <div className="mt-3 h-6 text-center sm:mt-4 sm:h-5">
          {submitError ? <p className="text-sm text-status-error-text">{submitError}</p> : null}
        </div>
      </div>
    </OnboardingShell>
  );
}
