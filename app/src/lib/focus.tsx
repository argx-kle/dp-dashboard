/* Shared hover/focus target so the cluster map and the attention list light each other up. */

import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';

interface FocusState {
  focus: string | null;
  setFocus: (urn: string | null) => void;
}

const FocusContext = createContext<FocusState>({ focus: null, setFocus: () => {} });

export function FocusProvider({ children }: { children: ReactNode }) {
  const [focus, setFocus] = useState<string | null>(null);
  const value = useMemo(() => ({ focus, setFocus }), [focus]);
  return <FocusContext.Provider value={value}>{children}</FocusContext.Provider>;
}

export function useFocusTarget(): FocusState {
  return useContext(FocusContext);
}
