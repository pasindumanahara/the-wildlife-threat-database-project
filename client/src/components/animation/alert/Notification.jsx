import {useEffect} from "react";
import {
  AnimatePresence,
  domAnimation,
  LazyMotion,
  m,
  useReducedMotion,
} from "framer-motion";
import {Alert} from "./Alert";

export default function Notification({notice, onDismiss}) {
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(onDismiss, 2500);
    return () => window.clearTimeout(timer);
  }, [notice, onDismiss]);

  const hidden = {opacity: 0, y: reducedMotion ? 0 : "-120%"};
  return (
    <div className="font-display pointer-events-none fixed inset-x-0 top-[max(0.75rem,env(safe-area-inset-top))] z-50 mx-auto max-w-md px-3">
      <LazyMotion features={domAnimation}>
        <AnimatePresence mode="wait">
          {notice && (
            <m.div
              key={notice.id}
              initial={hidden}
              animate={{opacity: 1, y: 0}}
              exit={hidden}
              transition={{duration: reducedMotion ? 0 : 0.2, ease: "easeOut"}}
            >
              <Alert {...notice} onDismiss={onDismiss} />
            </m.div>
          )}
        </AnimatePresence>
      </LazyMotion>
    </div>
  );
}
