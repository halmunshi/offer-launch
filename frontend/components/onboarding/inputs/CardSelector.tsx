import type { LucideIcon } from "lucide-react";

type CardOption = {
  id: string;
  icon: LucideIcon;
  title: string;
  description: string;
};

type CardSelectorProps = {
  options: CardOption[];
  value: string | null;
  onChange: (id: string) => void;
};

export function CardSelector({ options, value, onChange }: CardSelectorProps) {
  return (
    <div className="grid grid-cols-1 gap-2.5 text-left sm:grid-cols-2 sm:gap-3">
      {options.map((option) => {
        const selected = value === option.id;
        const Icon = option.icon;

        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onChange(option.id)}
            className={`rounded-card border-[1.5px] bg-card p-3 text-center transition-all duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] sm:p-3.5 ${
              selected
                ? "border-orange bg-selected text-primary shadow-[0_0_0_1px_var(--orange)]"
                : "border-border text-secondary hover:-translate-y-px hover:border-[#d4d0cc] hover:text-primary"
            }`}
          >
            <Icon
              className={`mx-auto mb-2 h-5 w-5 sm:h-6 sm:w-6 ${selected ? "text-orange" : "text-secondary"}`}
              strokeWidth={1.8}
            />
            <p className="mb-1 text-sm font-semibold tracking-[-0.01em] text-primary sm:text-[15px]">{option.title}</p>
            <p className="text-xs leading-relaxed text-secondary">{option.description}</p>
          </button>
        );
      })}
    </div>
  );
}
