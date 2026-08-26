import { useRef, useState, useCallback, createContext, useContext } from "react";
import { X, CheckCircle, AlertTriangle, Info } from "lucide-react";

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

  const toast = useCallback((message: string, type: ToastType = "info") => {
    const id = ++nextIdRef.current;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const dismiss = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const icons = {
    success: <CheckCircle className="size-4 text-emerald-400" />,
    error: <AlertTriangle className="size-4 text-red-400" />,
    info: <Info className="size-4 text-blue-400" />,
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="flex items-center gap-3 rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm text-slate-200 shadow-lg transition-all duration-300 ease-in-out translate-x-0 opacity-100"
          >
            {icons[t.type]}
            <span className="flex-1">{t.message}</span>
            <button onClick={() => dismiss(t.id)} className="text-slate-500 hover:text-slate-300">
              <X className="size-3" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
