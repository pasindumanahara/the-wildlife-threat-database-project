import {m, useReducedMotion} from "framer-motion";

const stepNames = ["Choose account type", "Enter details", "Add a profile photo"];

export function SignupProgress({step}) {
  const reduceMotion = useReducedMotion();
  return (
    <div className="mb-6">
      <p className="mb-2 flex flex-wrap items-baseline gap-x-2 text-sm">
        <span className="font-semibold">Step {step} of 3</span>
        <span className="text-zinc-600">{stepNames[step - 1]}</span>
      </p>
      <div aria-hidden="true" className="flex gap-2">
        {stepNames.map(function renderSegment(name, index) {
          return (
            <span key={name} className="h-1 flex-1 overflow-hidden rounded-full bg-zinc-200">
              <m.span
                className="block h-full origin-left rounded-full bg-twtdbp-crimson"
                initial={false}
                animate={{scaleX: index < step ? 1 : 0}}
                transition={{type: "tween", duration: reduceMotion ? 0 : 0.3, ease: "easeOut"}}
              />
            </span>
          );
        })}
      </div>
    </div>
  );
}
