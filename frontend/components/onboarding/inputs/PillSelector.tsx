type PillOption = {
  id: string;
  label: string;
};

type PillSelectorProps = {
  options: PillOption[];
  value: string | string[] | null;
  onChange: (value: string | string[]) => void;
  allowOther?: boolean;
  otherPlaceholder?: string;
  otherValue?: string;
  onOtherChange?: (value: string) => void;
};

export function PillSelector({
  options,
  value,
  onChange,
  allowOther = false,
  otherPlaceholder,
  otherValue = "",
  onOtherChange,
}: PillSelectorProps) {
  const isMulti = Array.isArray(value);
  const selectedSet = new Set(Array.isArray(value) ? value : value ? [value] : []);
  const otherSelected = allowOther && selectedSet.has("other");

  function toggle(id: string) {
    if (isMulti) {
      const next = new Set(selectedSet);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      onChange(Array.from(next));
      return;
    }

    onChange(id);
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap justify-center gap-2 sm:mb-7">
        {options.map((option) => {
          const selected = selectedSet.has(option.id);
          return (
            <button
              key={option.id}
              type="button"
              onClick={() => toggle(option.id)}
              className={`rounded-pill border-[1.5px] px-3.5 py-2 text-xs font-medium transition-all duration-200 ease-[cubic-bezier(0.22,1,0.36,1)] sm:px-[18px] sm:py-[10px] sm:text-[13px] ${
                selected
                  ? "border-orange bg-selected text-primary shadow-[0_0_0_1px_var(--orange)]"
                  : "border-border bg-card text-secondary hover:-translate-y-px hover:border-[#d4d0cc] hover:text-primary"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>

      {allowOther ? (
        <div
            className={`overflow-hidden transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] ${
              otherSelected ? "mb-7 max-h-[72px] opacity-100" : "mb-0 max-h-0 opacity-0"
            }`}
          >
          <input
            type="text"
            value={otherValue}
            onChange={(event) => onOtherChange?.(event.target.value)}
            placeholder={otherPlaceholder}
            className="w-full rounded-input border-[1.5px] border-border bg-card px-4 py-3 text-[14px] text-primary outline-none transition-all placeholder:text-muted focus:border-orange focus:ring-4 focus:ring-orange/10 sm:px-[18px] sm:py-[13px]"
          />
        </div>
      ) : null}
    </div>
  );
}
