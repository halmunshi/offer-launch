import { useLayoutEffect, useRef } from "react";

type TextAreaProps = {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  minRows?: number;
  submitOnEnter?: boolean;
  onEnter?: () => void;
};

export function TextArea({
  label,
  placeholder,
  value,
  onChange,
  error,
  minRows = 4,
  submitOnEnter = false,
  onEnter,
}: TextAreaProps) {
  const ref = useRef<HTMLTextAreaElement | null>(null);

  useLayoutEffect(() => {
    if (!ref.current) {
      return;
    }
    ref.current.style.height = "auto";
    ref.current.style.height = `${ref.current.scrollHeight}px`;
  }, [value]);

  return (
    <div className="space-y-2 text-left">
      {label ? <label className="block text-sm font-medium text-secondary">{label}</label> : null}
      <textarea
        ref={ref}
        rows={minRows}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (!submitOnEnter) {
            return;
          }
          if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
            event.preventDefault();
            onEnter?.();
          }
        }}
        placeholder={placeholder}
        className="w-full resize-none rounded-input border-[1.5px] border-border bg-card px-4 py-3 text-[14px] text-primary outline-none transition-all placeholder:text-muted focus:border-orange sm:px-[18px] sm:py-[13px]"
      />
      {error ? <p className="text-sm text-status-error-text">{error}</p> : null}
    </div>
  );
}
