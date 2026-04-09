import { X } from "lucide-react";
import type { ReactNode } from "react";

type OnboardingShellProps = {
  progress: number;
  activeDot: number;
  totalDots: number;
  children: ReactNode;
  showLogo?: boolean;
  visualVariant?: "default" | "offer";
  onExit?: () => void;
  exitLabel?: string;
};

export function OnboardingShell({
  progress,
  activeDot,
  totalDots,
  children,
  showLogo = true,
  visualVariant = "default",
  onExit,
  exitLabel = "Exit",
}: OnboardingShellProps) {
  void progress;
  const waveClassName = visualVariant === "offer" ? "wave wave--offer" : "wave";

  return (
    <section className="relative flex h-[100dvh] w-full flex-col items-center justify-center overflow-hidden bg-page">
      {showLogo ? (
        <div className="absolute top-5 z-20 select-none text-[17px] font-extrabold tracking-[-0.02em] sm:top-7 sm:text-[18px]">
          <span className="text-primary">Offer</span>
          <span className="text-[#f26522]">Launch</span>
        </div>
      ) : null}

      {onExit ? (
        <button
          type="button"
          onClick={onExit}
          aria-label={exitLabel}
          className="absolute right-4 top-4 z-20 inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card/90 text-secondary transition-all hover:border-[#d4d0cc] hover:text-primary sm:right-6 sm:top-6"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      ) : null}

      <div className="relative z-10 w-full max-w-[620px] px-4 text-center sm:px-6">{children}</div>

      <div className={waveClassName} />

      <div className="absolute bottom-6 z-20 flex items-center gap-1.5 sm:bottom-8">
        {Array.from({ length: totalDots }).map((_, index) => {
          const isActive = index === activeDot;
          return (
            <span
              key={index}
              className={`transition-all duration-300 ${
                isActive
                  ? "h-[6px] w-[18px] rounded-[3px] bg-primary opacity-100"
                  : "h-[6px] w-[6px] rounded-full bg-muted opacity-60"
              }`}
            />
          );
        })}
      </div>
    </section>
  );
}
