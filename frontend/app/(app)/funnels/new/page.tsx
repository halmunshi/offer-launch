"use client";

import { useAuth } from "@clerk/nextjs";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { OnboardingShell } from "@/components/onboarding/OnboardingShell";
import { StepFunnelName } from "@/components/onboarding/steps/funnel/StepFunnelName";
import { StepFunnelType } from "@/components/onboarding/steps/funnel/StepFunnelType";
import { StepIntegrations } from "@/components/onboarding/steps/funnel/StepIntegrations";
import { StepStyle } from "@/components/onboarding/steps/funnel/StepStyle";
import type { FunnelSetupAnswers } from "@/components/onboarding/steps/funnel/types";
import { useOnboarding } from "@/hooks/useOnboarding";
import { api } from "@/lib/api";

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

const stepProgress = [10, 35, 60, 85];
const DEFERRED_EMBED_PLACEHOLDER = "User will provide embed link later. Use a placeholder for now.";

type WorkflowRunResponse = {
  funnel_id: string;
  job_ids: string[];
};

export default function NewFunnelPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { getToken } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [visualProgress, setVisualProgress] = useState<number | null>(null);

  const offerId = useMemo(() => searchParams.get("offerId")?.trim() ?? "", [searchParams]);

  const onboarding = useOnboarding<FunnelSetupAnswers>({
    totalSteps: 4,
    initialAnswers: {
      funnelName: "",
      funnelType: "",
      integrations: null,
      funnelStyle: "",
    },
  });

  useEffect(() => {
    if (!offerId) {
      router.replace("/dashboard");
    }
  }, [offerId, router]);

  async function launchBuilder() {
    if (!offerId) {
      return;
    }

    if (!onboarding.answers.funnelName || !onboarding.answers.funnelType || !onboarding.answers.funnelStyle) {
      return;
    }

    let integrationsPayload: Record<string, unknown> = {};
    if (onboarding.answers.funnelType === "lead_generation") {
      const lead = (onboarding.answers.integrations ?? {}) as {
        leadMagnetType?: string;
        leadMagnetDescription?: string;
        leadMagnetReady?: boolean;
      };
      integrationsPayload = {
        lead_magnet_type: lead.leadMagnetType ?? "",
        lead_magnet_description: lead.leadMagnetDescription ?? "",
        lead_magnet_ready: Boolean(lead.leadMagnetReady),
      };
    } else if (onboarding.answers.funnelType === "call_funnel") {
      const call = (onboarding.answers.integrations ?? {}) as {
        hasVsl?: boolean;
        vslEmbed?: string;
        calendarProvider?: string;
        calendarEmbed?: string;
      };
      const hasVsl = Boolean(call.hasVsl);
      integrationsPayload = {
        has_vsl: hasVsl,
        vsl_embed: hasVsl ? (call.vslEmbed?.trim() || DEFERRED_EMBED_PLACEHOLDER) : "",
        calendar_provider: call.calendarProvider ?? "",
        calendar_embed: call.calendarEmbed?.trim() || DEFERRED_EMBED_PLACEHOLDER,
      };
    } else {
      const direct = (onboarding.answers.integrations ?? {}) as {
        paymentProcessor?: string;
        paymentEmbed?: string;
      };
      integrationsPayload = {
        payment_processor: direct.paymentProcessor ?? "",
        payment_embed: direct.paymentEmbed?.trim() || DEFERRED_EMBED_PLACEHOLDER,
      };
    }

    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const token = await getToken();
      const response = await api.post<WorkflowRunResponse, Record<string, unknown>>(
        "/workflow-runs",
        {
          offer_id: offerId,
          funnel_name: onboarding.answers.funnelName,
          funnel_type: onboarding.answers.funnelType,
          funnel_style: onboarding.answers.funnelStyle,
          integrations: integrationsPayload,
        },
        token,
      );

      setVisualProgress(100);

      const firstJobId = Array.isArray(response.job_ids) && response.job_ids.length > 0 ? response.job_ids[0] : "";
      window.setTimeout(() => {
        if (firstJobId) {
          router.push(`/builder/${response.funnel_id}?jobId=${firstJobId}`);
          return;
        }
        router.push(`/builder/${response.funnel_id}`);
      }, 260);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Unable to launch builder.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <OnboardingShell
      progress={visualProgress ?? stepProgress[onboarding.currentStep] ?? 0}
      activeDot={onboarding.currentStep}
      totalDots={4}
      showLogo={false}
      visualVariant="offer"
      onExit={() => router.push("/funnels")}
      exitLabel="Exit setup"
    >
      <div className="min-h-[560px] sm:min-h-[460px]">
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
              <StepFunnelName
                answers={onboarding.answers}
                setAnswer={onboarding.setAnswer}
                next={onboarding.next}
                onBackToFunnels={() => router.push("/funnels")}
              />
            ) : null}

            {onboarding.currentStep === 1 ? (
              <StepFunnelType
                answers={onboarding.answers}
                setAnswer={onboarding.setAnswer}
                next={onboarding.next}
                onBack={onboarding.back}
              />
            ) : null}

            {onboarding.currentStep === 2 ? (
              <StepIntegrations
                answers={onboarding.answers}
                setAnswer={onboarding.setAnswer}
                next={onboarding.next}
                back={onboarding.back}
                entryDirection={onboarding.direction}
              />
            ) : null}

            {onboarding.currentStep === 3 ? (
              <StepStyle
                answers={onboarding.answers}
                setAnswer={onboarding.setAnswer}
                back={onboarding.back}
                onLaunch={launchBuilder}
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
