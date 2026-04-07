"use client";

import { useAuth } from "@clerk/nextjs";
import { useUser } from "@clerk/nextjs";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { OnboardingShell } from "@/components/onboarding/OnboardingShell";
import { StepBusinessType } from "@/components/onboarding/steps/user/StepBusinessType";
import { StepIndustry } from "@/components/onboarding/steps/user/StepIndustry";
import { StepName } from "@/components/onboarding/steps/user/StepName";
import { useOnboarding } from "@/hooks/useOnboarding";
import { api } from "@/lib/api";

const ONBOARDING_CACHE_PREFIX = "offerlaunch:onboarding:";

type UserOnboardingAnswers = {
  fullName: string;
  businessType: string;
  industry: string;
  customIndustry: string;
};

const industryLabels: Record<string, string> = {
  business_entrepreneurship: "Business & Entrepreneurship",
  marketing_advertising: "Marketing & Advertising",
  real_estate: "Real Estate",
  finance_investing: "Finance & Investing",
  health_fitness: "Health & Fitness",
  beauty_aesthetics: "Beauty & Aesthetics",
  relationships_dating: "Relationships & Dating",
  personal_development: "Personal Development",
  education_coaching: "Education & Coaching",
  legal_professional_services: "Legal & Professional Services",
  ecommerce_retail: "E-commerce & Retail",
  technology_saas: "Technology & SaaS",
  local_services: "Local Services",
  other: "Other",
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

export default function UserOnboardingPage() {
  const router = useRouter();
  const { getToken, userId } = useAuth();
  const { user } = useUser();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [visualProgress, setVisualProgress] = useState<number | null>(null);

  const onboarding = useOnboarding<UserOnboardingAnswers>({
    totalSteps: 3,
    initialAnswers: {
      fullName: "",
      businessType: "",
      industry: "",
      customIndustry: "",
    },
  });

  const resolvedIndustry = useMemo(() => {
    if (onboarding.answers.industry === "other") {
      return onboarding.answers.customIndustry.trim() || "Other";
    }

    return industryLabels[onboarding.answers.industry] ?? "";
  }, [onboarding.answers.customIndustry, onboarding.answers.industry]);

  async function handleFinish() {
    const finalIndustry = resolvedIndustry;
    if (!finalIndustry || finalIndustry.trim().length < 2) {
      return;
    }

    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const token = await getToken();
      const normalizedFullName =
        onboarding.answers.fullName.trim() ||
        user?.fullName?.trim() ||
        user?.firstName?.trim() ||
        "User";

      await api.patch("/users/me", {
        fullName: normalizedFullName,
        businessType: onboarding.answers.businessType,
        industry: finalIndustry,
      }, token);

      if (userId) {
        sessionStorage.setItem(`${ONBOARDING_CACHE_PREFIX}${userId}`, "complete");
      }

      setVisualProgress(100);
      window.setTimeout(() => {
        router.push("/dashboard");
      }, 260);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Unable to save onboarding details.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <OnboardingShell
      progress={visualProgress ?? onboarding.progress}
      activeDot={onboarding.currentStep}
      totalDots={onboarding.totalSteps}
    >
      <div className="min-h-[500px] sm:min-h-[420px]">
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
              <StepName
                value={onboarding.answers.fullName}
                onChange={(value) => onboarding.setAnswer("fullName", value)}
                onContinue={onboarding.next}
              />
            ) : null}

            {onboarding.currentStep === 1 ? (
              <StepBusinessType
                value={onboarding.answers.businessType || null}
                onChange={(value) => onboarding.setAnswer("businessType", value)}
                onBack={onboarding.back}
                onContinue={onboarding.next}
              />
            ) : null}

            {onboarding.currentStep === 2 ? (
              <StepIndustry
                selectedIndustry={onboarding.answers.industry || null}
                customIndustry={onboarding.answers.customIndustry}
                onIndustryChange={(value) => onboarding.setAnswer("industry", value)}
                onCustomIndustryChange={(value) => onboarding.setAnswer("customIndustry", value)}
                onBack={onboarding.back}
                onFinish={handleFinish}
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
