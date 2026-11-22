import {useState} from "react";
import {LazyMotion, domAnimation, m, useReducedMotion} from "framer-motion";
import wildlife from "../assets/images/elephant-family-winding-river.png";
import logo from "../assets/logos/TWTDBP-Black.svg";
import {Button} from "../components/common/Button";
import {SignupProgress} from "../components/auth/signup/SignupProgress";
import {AccountTypeStep} from "../components/auth/signup/AccountTypeStep";
import {SignupDetailsStep} from "../components/auth/signup/SignupDetailsStep";
import {ProfilePhotoStep} from "../components/auth/signup/ProfilePhotoStep";
import {LoginImagePanel} from "../components/auth/login/LoginImagePanel";
import {ArrowLeft} from "lucide-react";
import {Link} from "react-router-dom";
import {register} from "../services/auth";
import {ElephantLoader} from "../components/animation/loader/ElephantLoader";
import {useDashboardTransition} from "../components/animation/loader/useDashboardTransition";
import {
  validateEmail,
  validateNIC,
  validateOfficerForm,
  validatePassword,
  validateProfilePhoto,
} from "../utils/signupDataValidation";

export function SignupPage({notify, dismiss}) {
  const {openingDashboard, openDashboard} = useDashboardTransition();
  const [step, setStep] = useState(1);
  const [slideDirection, setSlideDirection] = useState(null);
  const reduceMotion = useReducedMotion();
  const [account, setAccount] = useState("");
  const [draft, setDraft] = useState({countryCode: "LK"});
  const [documentFile, setDocumentFile] = useState(null);
  const [photo, setPhoto] = useState(null);
  const [busy, setBusy] = useState(false);
  const [validating, setValidating] = useState(false);
  const officer = account === "officer";
  const titles = [
    "Create an account",
    officer ? "Enter your officer details" : "Enter your details",
    "Add a profile photo (optional)",
  ];
  const descriptions = [
    "Choose the account type that applies to you",
    officer
      ? "Add your personal and work information. You must upload a document that verifies your government role"
      : "Add your personal information and choose your login details",
    "A profile photo is optional but we encourage you to use one",
  ];

  function handleAccount(event) {
    setAccount(event.target.value);
    if (event.target.value === "officer") {
      setDraft(function setOfficerDesignation(previous) {
        return {
          ...previous,
          designation: previous.designation || "Wildlife officer",
        };
      });
    }
    dismiss();
  }
  function handleField(event) {
    const {name, value} = event.target;
    setDraft(function update(previous) {
      return {...previous, [name]: value};
    });
  }
  function handleDocument(file) {
    setDocumentFile(file);
    dismiss();
  }
  async function handlePhoto(file) {
    setValidating(true);
    try {
      const result = await validateProfilePhoto(file);
      if (!result.isValid) return notify("error", result.error);
      setPhoto(file);
      dismiss();
    } catch {
      notify(
        "error",
        "Could not read the profile photo. Choose the file again.",
      );
    } finally {
      setValidating(false);
    }
  }
  function goBack() {
    dismiss();
    setSlideDirection("back");
    setStep(step - 1);
  }
  async function handleSubmit(event) {
    event.preventDefault();
    if (validating || busy) return;
    if (step === 1 && !account)
      return notify("error", "Choose an account type to continue.");
    if (step === 2) {
      const form = event.currentTarget;
      const missing = Array.from(form.elements).find(
        (field) => field.required && !field.value.trim(),
      );
      if (missing) {
        missing.focus();
        const label = missing.labels?.[0]?.textContent.trim();
        return notify("error", `${label || "This field"} is required.`);
      }

      setValidating(true);
      try {
        const errors = officer
          ? (
              await validateOfficerForm({
                ...draft,
                verificationDocument: documentFile,
              })
            ).errors
          : {
              nic: validateNIC(draft.nic).error,
              email: validateEmail(draft.email).error,
              password: validatePassword(draft.password).error,
            };
        const message = Object.values(errors).find(Boolean);
        if (message) return notify("error", message);
      } catch {
        return notify(
          "error",
          "Could not read the verification document. Choose the file again.",
        );
      } finally {
        setValidating(false);
      }
    }
    dismiss();
    if (step < 3) {
      setSlideDirection("forward");
      setStep(step + 1);
    } else {
      const payload = new FormData();
      payload.append("account", account);
      for (const [key, value] of Object.entries(draft)) payload.append(key, value);
      if (photo) payload.append("photo", photo);
      if (officer && documentFile) payload.append("document", documentFile);
      setBusy(true);
      try {
        const result = await register(payload);
        notify("success", "Account created successfully.");
        openDashboard({replace: true, state: {
          notice: result.officerStatus === "pending" ? "Officer verification is pending." : "",
        }});
      } catch (cause) {
        notify("error", cause.message);
      } finally {
        setBusy(false);
      }
    }
  }
  if (openingDashboard) return <ElephantLoader />;

  return (
    <main className="grid min-h-dvh place-items-center overflow-x-hidden bg-zinc-100 p-4 font-display sm:p-8">
      <section
        aria-labelledby="signup-title"
        className={
          "mx-auto grid w-full min-w-0 rounded-[1.75rem] bg-white text-twtdbp-ebony shadow-xl " +
          (step === 1 ? "max-w-5xl md:grid-cols-2 md:p-5" : "max-w-6xl lg:p-5")
        }
      >
        {step === 1 && <LoginImagePanel imageSrc={wildlife} />}
        <LazyMotion features={domAnimation}>
          <div className="my-auto min-w-0 px-6 py-8 sm:px-10 lg:px-12">
            <img src={logo} alt="TWTDBP" className="mb-6 w-52 lg:hidden" />
            {step > 1 && (
              <button
                type="button"
                onClick={goBack}
                disabled={validating || busy}
                aria-label="Go back"
                className="mb-4 inline-flex items-center gap-2 rounded-lg px-2 py-1 text-sm font-semibold text-zinc-700 hover:bg-zinc-200 hover:text-zinc-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-twtdbp-crimson"
              >
                <ArrowLeft aria-hidden="true" className="size-4" />
                Back
              </button>
            )}
            <SignupProgress step={step} />
            <m.div
              key={step}
              initial={
                slideDirection && !reduceMotion
                  ? {x: slideDirection === "back" ? -20 : 20}
                  : false
              }
              animate={{x: 0}}
              transition={{type: "tween", duration: 0.18, ease: "easeOut"}}
            >
              <h1
                id="signup-title"
                className="text-4xl font-semibold tracking-tight"
              >
                {titles[step - 1]}
              </h1>
              <p className="mt-2 text-sm text-zinc-600">
                {descriptions[step - 1]}
              </p>
              <form
                noValidate
                method="post"
                onSubmit={handleSubmit}
                className={
                  "mt-5 space-y-5 pt-3 " + (step >= 2 ? "@container" : "")
                }
              >
                {step === 1 && (
                  <AccountTypeStep account={account} onChange={handleAccount} />
                )}
                {step === 2 && (
                  <fieldset disabled={validating || busy} className="min-w-0">
                    <SignupDetailsStep
                      officer={officer}
                      draft={draft}
                      onChange={handleField}
                      documentFile={documentFile}
                      onDocument={handleDocument}
                    />
                  </fieldset>
                )}
                {step === 3 && (
                  <fieldset disabled={validating || busy} className="min-w-0">
                    <ProfilePhotoStep
                      photo={photo}
                      onPhoto={handlePhoto}
                      fullName={draft.fullName ?? ""}
                      email={draft.email ?? ""}
                      accountType={account}
                    />
                  </fieldset>
                )}
                <div
                  className={`flex items-center gap-3 ${step === 1 ? "" : "justify-end"}`}
                >
                  {step > 1 && (
                    <Button
                      type="button"
                      onClick={goBack}
                      disabled={validating || busy}
                      size={48}
                      className="gap-2 border border-zinc-300 bg-white text-zinc-800 hover:!bg-zinc-100 hover:!text-zinc-900"
                    >
                      <ArrowLeft aria-hidden="true" className="size-4" />
                      Back
                    </Button>
                  )}
                  <Button
                    type="submit"
                    disabled={validating || busy}
                    size={48}
                    className={`text-white! ${step === 1 ? "w-full" : ""}`}
                  >
                    {busy ? "Creating account..." : step === 3 ? "Create account" : "Continue"}
                  </Button>
                </div>
              </form>
              {step === 1 && (
                <p className="mt-4 text-center text-sm text-zinc-600">
                  Already have an account?{" "}
                  <Link
                    to="/login"
                    className="font-semibold text-twtdbp-ebony underline underline-offset-4 hover:font-bold"
                  >
                    Log in
                  </Link>
                </p>
              )}
            </m.div>
          </div>
        </LazyMotion>
      </section>
    </main>
  );
}
