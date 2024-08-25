import { VERBA_PORT } from "./config";

export const detectHost = async (): Promise<string> => {
  const checkUrl = async (url: string): Promise<boolean> => {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP status ${response.status}`);
      }
      return true;
    } catch (error) {
      console.error(`Failed to fetch from ${url}:`, error);
      return false;
    }
  };

  const localUrl = `http://localhost:${VERBA_PORT}/api/health`;
  const rootUrl = "/api/health";

  const isLocalHealthy = await checkUrl(localUrl);
  if (isLocalHealthy) {
    return `http://localhost:${VERBA_PORT}`;
  }

  const isRootHealthy = await checkUrl(rootUrl);
  if (isRootHealthy) {
    return "";
  }

  throw new Error("Both health checks failed, please check the Verba Server");
};
