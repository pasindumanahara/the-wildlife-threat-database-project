import {useState} from "react";
import {OfficerFields} from "./OfficerFields";
import {SignupField} from "./SignupField";
import {AddressFields} from "./AddressFields";
import {FileUpload} from "../../common/FileUpload";
import {Eye, EyeOff} from "lucide-react";

export function SignupDetailsStep({
  officer,
  draft,
  onChange,
  documentFile,
  onDocument,
}) {
  const [visible, setVisible] = useState(false);
  const props = {draft, onChange};

  function togglePassword() {
    setVisible(!visible);
  }

  return (
    <div className="grid min-w-0 gap-5 @xl:grid-cols-2 @xl:gap-6">
      <fieldset className="min-w-0 space-y-4 rounded-2xl border border-zinc-200 p-4 sm:p-5">
        <legend className="px-1 font-semibold">Personal information</legend>
        <SignupField
          {...props}
          name="fullName"
          label="Full name"
          autoComplete="name"
        />
        <SignupField
          {...props}
          name="nic"
          label="NIC number"
          autoComplete="off"
        />
        <SignupField
          {...props}
          name="mobile"
          label="Mobile number"
          countryCode
          autoComplete="section-personal tel-national"
        />
        <div className="space-y-2">
          <p className="text-sm font-medium">
            {officer ? "Personal address" : "Address"}
          </p>
          <AddressFields {...props} autoCompletePrefix="section-personal " />
        </div>
      </fieldset>
      <div className="min-w-0 space-y-5">
        {officer && <OfficerFields {...props} />}
        <fieldset className="min-w-0 space-y-4 rounded-2xl border border-zinc-200 p-4 sm:p-5">
          <legend className="px-1 font-semibold">Login details</legend>
          <div className="grid gap-3">
            <SignupField
              {...props}
              name="username"
              label="Username"
              autoComplete="username"
            />
            <SignupField
              {...props}
              name="email"
              label="Email address"
              type="email"
              autoComplete="email"
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="signup-password"
              className="block text-sm font-medium"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="signup-password"
                aria-describedby="signup-password-hint"
                name="password"
                value={draft.password ?? ""}
                onChange={onChange}
                type={visible ? "text" : "password"}
                autoComplete="new-password"
                required
                className="twtdbp-input pr-12"
              />
              <button
                type="button"
                onClick={togglePassword}
                aria-label={visible ? "Hide password" : "Show password"}
                aria-pressed={visible}
                className="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-lg text-zinc-500 hover:text-zinc-900 focus-visible:outline-2 focus-visible:outline-inset focus-visible:outline-twtdbp-crimson"
              >
                {visible ? (
                  <EyeOff aria-hidden="true" className="size-5" />
                ) : (
                  <Eye aria-hidden="true" className="size-5" />
                )}
              </button>
            </div>
            <p id="signup-password-hint" className="text-xs text-zinc-600">
              Use atleast 8 characters with uppercase and lowercase letters, a
              number, and a symbol. No spaces.
            </p>
          </div>
        </fieldset>
        {officer && (
          <fieldset className="min-w-0 space-y-3 rounded-2xl border border-zinc-200 p-4 sm:p-5">
            <legend className="px-1 font-semibold">Officer verification</legend>
            <p className="text-sm font-medium">Verification document</p>
            <p className="text-sm text-zinc-600">
              Upload a document that verifies your government role
            </p>
            <FileUpload
              file={documentFile}
              type="document"
              label="Choose a verification document"
              description=""
              onSelect={onDocument}
              accept={".pdf,.jpg,.jpeg,.png"}
            />
          </fieldset>
        )}
      </div>
    </div>
  );
}
