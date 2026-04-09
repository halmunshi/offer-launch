type TextInputProps = {
  label?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  autoFocus?: boolean;
};

export function TextInput({ label, placeholder, value, onChange, error, autoFocus }: TextInputProps) {
  return (
    <div className="space-y-2 text-left">
      {label ? <label className="block text-sm font-medium text-secondary">{label}</label> : null}
      <input
        autoFocus={autoFocus}
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full rounded-input border-[1.5px] border-border bg-card px-4 py-3 text-[14px] text-primary outline-none transition-all placeholder:text-muted focus:border-orange sm:px-[18px] sm:py-[13px]"
      />
      {error ? <p className="text-sm text-status-error-text">{error}</p> : null}
    </div>
  );
}
