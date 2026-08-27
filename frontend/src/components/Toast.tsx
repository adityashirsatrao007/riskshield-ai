import {
  useRef,
  useState,
  useCallback,
  createContext,
  useContext,
} from "react";
import { X, CheckCircle, AlertTriangle, Info } from "lucide-react";
import { clsx } from "clsx";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

const ToastContext = createContext<{
  toast: (message: string, type?: ToastType) => void;
}>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextIdRef = useRef(0);

  const toast = useCallback(
    (message: string, type: ToastType = "info") => {
      const id = ++nextIdRef.current;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    },
    []
  );

  const dismiss = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const config: Record<
    ToastType,
    { icon: React.ReactNode; gradient: string; border: string }
  > = {
    success: {
      icon: <CheckCircle className="size-4 text-emerald-400" />,
      gradient: "from-emerald-500/10 to-transparent",
      border: "border-emerald-500/20",
    },
    error: {
      icon: <AlertTriangle className="size-4 text-red-400" />,
      gradient: "from-red-500/10 to-transparent",
      border: "border-red-500/20",
    },
    info: {
      icon: <Info className="size-4 text-blue-400" />,
      gradient: "from-blue-500/10 to-transparent",
      border: "border-blue-500/20",
    },
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={clsx(
              "animate-slide-right glass-card flex min-w-[280px] items-center gap-3 rounded-xl px-4 py-3 text-sm text-slate-200 shadow-2xl",
              config[t.type].border
            )}
          >
            <div
              className={clsx(
                "absolute inset-0 rounded-xl bg-gradient-to-r opacity-50",
                config[t.type].gradient
              )}
            />
            <div className="relative">{config[t.type].icon}</div>
            <span className="relative flex-1">{t.message}</span>
            <button
              onClick={() => dismiss(t.id)}
              className="relative text-slate-500 hover:text-slate-300"
            >
              <X className="size-3" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
