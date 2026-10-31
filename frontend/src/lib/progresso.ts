import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import type { Progresso } from "./types";

export function useProgresso() {
  return useQuery({
    queryKey: ["progresso"],
    queryFn: () => api.get<Progresso>("/progresso"),
  });
}
