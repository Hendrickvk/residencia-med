import { useEffect, useState } from "react";

export function useDebounced<T>(valor: T, atrasoMs = 250): T {
  const [debounced, setDebounced] = useState(valor);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(valor), atrasoMs);
    return () => clearTimeout(id);
  }, [valor, atrasoMs]);
  return debounced;
}
