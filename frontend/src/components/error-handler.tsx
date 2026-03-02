"use client";

import { useEffect } from "react";

/**
 * Prevents unhandled promise rejections (e.g. Event from failed script load)
 * from showing Next.js "[object Event]" runtime error overlay.
 */
export function ErrorHandler() {
  useEffect(() => {
    const onUnhandled = (e: PromiseRejectionEvent) => {
      const reason = e?.reason;
      const isEventObject =
        reason &&
        typeof reason === "object" &&
        // plain Event or subclass
        ((reason as Event).type !== undefined ||
          "target" in reason ||
          Object.prototype.toString.call(reason) === "[object Event]");

      const isNonError =
        reason &&
        typeof reason === "object" &&
        !(reason instanceof Error) &&
        !("stack" in (reason as any));

      if (isEventObject || isNonError || String(reason) === "[object Event]") {
        // Swallow noisy dev overlay for non-Error rejections (e.g. script/network events)
        e.preventDefault();
        // Still log to the console for debugging when needed
        console.warn("Suppressed unhandled rejection:", reason);
      }
    };
    window.addEventListener("unhandledrejection", onUnhandled);
    return () => window.removeEventListener("unhandledrejection", onUnhandled);
  }, []);
  return null;
}
