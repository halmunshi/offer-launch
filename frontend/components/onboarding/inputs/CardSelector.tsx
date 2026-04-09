import type { ComponentType, ReactNode } from "react";

type CardOption = {
  id: string;
  icon?: ComponentType<{ className?: string; strokeWidth?: number }>;
  title: string;
  description?: string;
  hint?: string;
  preview?: ReactNode;
  titleClassName?: string;
  cardClassName?: string;
  descriptionClassName?: string;
};

type CardSelectorProps = {
  options: CardOption[];
  value: string | null;
  onChange: (id: string) => void;
  layout?: "grid" | "stack" | "row" | "grid-3";
  density?: "default" | "compact";
};

export function CardSelector({
  options,
  value,
  onChange,
  layout = "grid",
  density = "default",
}: CardSelectorProps) {
  const containerClassName =
    layout === "stack"
      ? "grid grid-cols-1 gap-2.5 text-left sm:gap-3"
      : layout === "grid-3"
        ? "grid grid-cols-1 gap-2.5 text-left sm:grid-cols-3 sm:gap-3"
      : layout === "row"
        ? "grid auto-cols-[minmax(132px,1fr)] grid-flow-col gap-2.5 overflow-x-auto pb-1 pt-1 text-left sm:auto-cols-fr sm:gap-3"
        : "grid grid-cols-1 gap-2.5 text-left sm:grid-cols-2 sm:gap-3";

  const isCompact = density === "compact";

  return (
    <div className={containerClassName}>
      {options.map((option) => {
        const selected = value === option.id;
        const Icon = option.icon;

        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onChange(option.id)}
            data-selected={selected}
            className={`rounded-card border-[1.5px] bg-card text-center transition-all duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              isCompact ? "p-2.5 sm:p-3" : "p-3 sm:p-3.5"
            } ${
              selected
                ? "border-orange bg-selected text-primary shadow-[inset_0_0_0_1px_var(--orange)]"
                : "border-border text-secondary hover:-translate-y-px hover:border-[#d4d0cc] hover:text-primary"
            } ${option.cardClassName ?? ""}`}
          >
            {option.preview ? (
              <div className="mb-2">{option.preview}</div>
            ) : Icon ? (
              <span className={`mx-auto flex items-center justify-center gap-0.5 ${isCompact ? "mb-1.5" : "mb-2"}`}>
                <Icon
                  className={`${isCompact ? "h-4 w-4 sm:h-5 sm:w-5" : "h-5 w-5 sm:h-6 sm:w-6"} ${selected ? "text-orange" : "text-secondary"}`}
                  strokeWidth={1.8}
                />
              </span>
            ) : null}
            <p className={`tracking-[-0.01em] text-primary ${isCompact ? "mb-0.5 text-[13px] font-semibold sm:text-sm" : "mb-1 text-sm font-semibold sm:text-[15px]"}`}>
              <span className={option.titleClassName}>{option.title}</span>
            </p>
            {option.description ? (
              <p className={`${isCompact ? "text-[11px] leading-snug sm:text-xs" : "text-xs leading-relaxed"} text-secondary ${option.descriptionClassName ?? ""}`}>
                {option.description}
              </p>
            ) : null}
            {option.hint ? (
              <p className={`${isCompact ? "mt-0.5 text-[11px] leading-snug sm:text-xs" : "mt-1 text-[11px] leading-relaxed sm:text-xs"} text-muted`}>
                {option.hint}
              </p>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
