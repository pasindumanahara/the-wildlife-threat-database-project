import {Select} from "../../common/Select";
import {CountryCodeSelect} from "../../common/CountryCodeSelect";

export function SignupField({label, name, draft, onChange, type = "text", autoComplete, options, countryCode = false, required = true}) {
  const props = {name, value: draft[name] ?? "", onChange, autoComplete, required, className: "twtdbp-input"};
  return (
    <label className="block min-w-0 space-y-2 text-sm font-medium">
      <span className="block">{label}{!required && " (optional)"}</span>
      {options ? (
        <Select name={name} value={draft[name] ?? ""} onChange={onChange} options={options} placeholder="Select your designation" required={required} />
      ) : countryCode ? (
        <div className="flex min-w-0 gap-2">
          <CountryCodeSelect value={draft.countryCode ?? "LK"} onChange={onChange} />
          <input {...props} type="tel" inputMode="tel" autoComplete={autoComplete} className="twtdbp-input min-w-0 flex-1" />
        </div>
      ) : type === "textarea" ? (
        <textarea {...props} rows={3} className="twtdbp-input min-h-24 resize-y py-3" />
      ) : <input {...props} type={type} />}
    </label>
  );
}
