import { VERBA_PORT } from "@/app/config";

export const getWebSocketApiHost = () => {
  if (process.env.NODE_ENV === "development") {
    return `ws://localhost:${VERBA_PORT}/ws/generate_stream`;
  }
  // If you're serving the app directly through FastAPI, generate the WebSocket URL based on the current location.
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${protocol}//${host}/ws/generate_stream`;
};
