export interface Offer {
  id: string;
  name: string;
  oneLiner: string;
  industry: string;
  pricePoint: string;
  status: string;
  intakeData: OfferIntakeData;
  funnelCount: number;
  createdAt: string;
}

export interface Funnel {
  id: string;
  offerId: string;
  workflowRunId: string | null;
  name: string;
  funnelType: "lead_generation" | "call_funnel" | "direct_sales";
  theme: string;
  status: "draft" | "generating" | "ready" | "error";
}

export interface FunnelProject {
  files: Record<string, { code: string }>;
  sessionSummary: string | null;
  boilerplateVersion: string;
}

export interface Job {
  id: string;
  workflowRunId: string;
  offerId: string;
  agentType: "copywriter" | "funnel_builder";
  status: "pending" | "running" | "done" | "error";
  progress: ProgressEvent[];
}

export interface ProgressEvent {
  type: string;
  stage: string;
  message: string;
  ts: string;
  done: boolean;
}

export interface User {
  id: string;
  email: string;
  fullName: string | null;
  avatarUrl: string | null;
  businessType: string | null;
  industry: string | null;
  plan: "free" | "standard" | "pro" | "agency";
  createdAt: string;
}

export interface UsageStats {
  funnelCount: number;
  offerCount: number;
  runsThisMonth: number;
}

export interface OfferIntakeData {
  offerName: string;
  offerOneLiner: string;
  pricePoint: string;
  deliverable: string;
  idealClient: string;
  painPoint: string;
  transformation: string;
}

export interface FunnelSetupData {
  funnelType: "lead_generation" | "call_funnel" | "direct_sales";
  integrations: FunnelIntegrations;
  themeDirection: string;
  copyStyle: string;
}

export interface FunnelIntegrations {
  leadMagnetReady?: boolean;
  leadMagnetType?: string;
  hasCalendar?: boolean;
  calendarProvider?: string;
  calendarEmbed?: string;
  hasPaymentProcessor?: boolean;
  paymentProcessor?: string;
  wantsUpsells?: boolean;
}
