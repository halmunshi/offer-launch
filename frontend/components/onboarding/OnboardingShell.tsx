import type { ReactNode } from "react";

type OnboardingShellProps = {
  progress: number;
  activeDot: number;
  totalDots: number;
  children: ReactNode;
};

export function OnboardingShell({ progress, activeDot, totalDots, children }: OnboardingShellProps) {
  void progress;

  return (
    <section className="relative flex h-[100dvh] w-full flex-col items-center justify-center overflow-hidden bg-page">
      <div className="absolute top-5 z-20 select-none text-[17px] font-extrabold tracking-[-0.02em] sm:top-7 sm:text-[18px]">
        <span className="text-primary">Offer</span>
        <span className="text-[#f26522]">Launch</span>
      </div>

      <div className="relative z-10 w-full max-w-[620px] px-4 text-center sm:px-6">{children}</div>

      <div className="wave" />

      <div className="absolute bottom-6 z-20 flex items-center gap-1.5 sm:bottom-8">
        {Array.from({ length: totalDots }).map((_, index) => {
          const isActive = index === activeDot;
          return (
            <span
              key={index}
              className={`transition-all duration-300 ${
                isActive
                  ? "h-[6px] w-[18px] rounded-[3px] bg-primary opacity-100"
                  : "h-[6px] w-[6px] rounded-full bg-muted opacity-25"
              }`}
            />
          );
        })}
      </div>
    </section>
  );
}
