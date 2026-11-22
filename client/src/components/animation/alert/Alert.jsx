import {AlertCircle, CircleCheck, X} from "lucide-react";

export function Alert({type, message, onDismiss}) {
  const error = type === "error";
  const Icon = error ? AlertCircle : CircleCheck;

  return (
    <div
      data-slot="alert"
      role={error ? "alert" : "status"}
      aria-atomic="true"
      className="font-display pointer-events-auto flex items-start gap-3 rounded-2xl border border-zinc-200 bg-white p-4 text-zinc-900 shadow-lg"
    >
      <Icon
        aria-hidden="true"
        className={
          error
            ? "size-5 shrink-0 text-twtdbp-crimson"
            : "size-5 shrink-0 text-emerald-600"
        }
      />
      <div className="min-w-0 flex-1">
        <p data-slot="alert-title" className="text-sm font-semibold">
          {error ? "Check your details" : "Success"}
        </p>
        <p data-slot="alert-description" className="mt-1 text-sm text-zinc-700">
          {message}
        </p>
      </div>
      <button
        data-slot="alert-action"
        type="button"
        aria-label="Dismiss notification"
        onClick={onDismiss}
        className="-m-2 grid size-9 shrink-0 place-items-center rounded-full text-zinc-600 hover:bg-zinc-100"
      >
        <X aria-hidden="true" className="size-4" />
      </button>
    </div>
  );
}
