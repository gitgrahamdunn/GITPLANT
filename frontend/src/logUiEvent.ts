import { postUiAuditEvent } from "./api";

const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
const isDev = env?.DEV === "true" || env?.MODE === "development";

export function logUiEvent(
  token: string | null,
  name: string,
  payload?: Record<string, unknown>,
): void {
  const entry = { name, payload: payload ?? {} };
  console.info("[ui-event]", entry);

  if (!isDev) {
    return;
  }

  void postUiAuditEvent(token, entry).catch((error) => {
    console.warn("failed to post ui audit", error);
  });
}
