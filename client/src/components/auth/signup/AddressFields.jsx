import {Link} from "lucide-react";
import {SignupField} from "./SignupField";
import {Select} from "../../common/Select";
import {SRI_LANKA_PROVINCES} from "../../../data/sriLankaLocations";

export function AddressFields({draft, onChange, prefix, autoCompletePrefix}) {
  const props = {draft, onChange};
  const fieldName = function getFieldName(name) {
    return prefix ? prefix + name : name;
  };

  return (
    <div className="space-y-3">
      <SignupField
        {...props}
        name={fieldName("AddressLine1")}
        label="Address line 1"
        autoComplete={autoCompletePrefix + "address-line1"}
      />
      <SignupField
        {...props}
        name={fieldName("AddressLine2")}
        label="Address line 2"
        required={false}
        autoComplete={autoCompletePrefix + "address-line2"}
      />
      <SignupField
        {...props}
        name={fieldName("AddressLine3")}
        label="Address line 3"
        required={false}
        autoComplete={autoCompletePrefix + "address-line3"}
      />
      <div className="grid gap-3 @sm:grid-cols-2">
        <SignupField
          {...props}
          name={fieldName("City")}
          label="City"
          autoComplete={autoCompletePrefix + "address-level2"}
        />
        <ProvinceField
          draft={draft}
          onChange={onChange}
          name={fieldName("Province")}
        />
      </div>
      <SignupField
        {...props}
        name={fieldName("PostalCode")}
        label="Postal code"
        autoComplete={autoCompletePrefix + "postal-code"}
      />
      <a
        href="https://slpost.gov.lk/postcode_new/"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-sm font-medium underline underline-offset-4 hover:text-twtdbp-crimson"
      >
        <Link aria-hidden="true" className="size-4" />
        Search your Postal Code
        <span className="sr-only"> (opens in a new tab)</span>
      </a>
    </div>
  );
}

function ProvinceField({draft, onChange, name}) {
  const provinces = SRI_LANKA_PROVINCES.map((province) => province.name);
  return (
    <label className="block min-w-0 space-y-2 text-sm font-medium">
      <span className="block">Province</span>
      <Select
        name={name}
        value={draft[name] || "Western Province"}
        onChange={onChange}
        options={provinces}
        required
      />
    </label>
  );
}
