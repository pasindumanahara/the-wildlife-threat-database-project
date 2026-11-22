export function AccountTypeStep({account, onChange}) {
  const choices = [
    ["regular", "Regular User", "Create a personal account"],
    [
      "officer",
      "Government Officer",
      "Create an account in your official capacity. You’ll need to upload a document that verifies your government role",
    ],
  ];
  return (
    <fieldset className="min-w-0 space-y-3">
      <legend className="sr-only">Account type</legend>
      {choices.map(function renderChoice([value, title, description]) {
        return (
          <label
            key={value}
            className="flex cursor-pointer items-start gap-3 rounded-xl border border-zinc-300 p-4 has-checked:border-twtdbp-crimson has-checked:bg-zinc-50 has-focus-visible:outline-2 has-focus-visible:outline-twtdbp-crimson"
          >
            <input
              type="radio"
              name="account"
              value={value}
              checked={account === value}
              onChange={onChange}
              required
              className="mt-1.5 shrink-0 accent-twtdbp-crimson"
            />
            <span className="min-w-0 flex-1">
              <strong className="block leading-5 font-semibold">{title}</strong>
              <span className="mt-1 block text-sm text-zinc-600">
                {description}
              </span>
            </span>
          </label>
        );
      })}
    </fieldset>
  );
}
