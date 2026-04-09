export type LeadMagnetIntegrations = {
  leadMagnetType: string;
  leadMagnetDescription: string;
  leadMagnetReady: boolean;
};

export type CallFunnelIntegrations = {
  hasVsl: boolean;
  vslEmbed: string;
  calendarProvider: string;
  calendarEmbed: string;
};

export type DirectSalesIntegrations = {
  paymentProcessor: string;
  paymentEmbed: string;
};

export type FunnelSetupAnswers = {
  funnelName: string;
  funnelType: string;
  integrations: LeadMagnetIntegrations | CallFunnelIntegrations | DirectSalesIntegrations | null;
  funnelStyle: string;
};

export type SetFunnelAnswer = <K extends keyof FunnelSetupAnswers>(
  key: K,
  value: FunnelSetupAnswers[K],
) => void;
