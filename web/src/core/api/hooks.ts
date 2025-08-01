

import { useEffect, useRef, useState } from "react";

import { env } from "~/env";

import type { DeerFlowConfig } from "../config";
import type { Replay } from "../messages";
import { useReplay } from "../replay";

import { fetchReplayTitle } from "./chat";
import { queryReplays } from "./replays";
import { resolveServiceURL } from "./resolve-service-url";

export function useReplays(): {
  replays: Replay[] | null;
  loading: boolean;
} {
  const [replays, setReplays] = useState<Array<Replay>>([]);
  const [loading, setLoading] = useState(true);
  const isMounted = useRef(false);

  useEffect(() => {
    if (env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY) {
      setLoading(false);
      return;
    }
    isMounted.current = true;
    queryReplays()
      .then((data) => {
        if (isMounted.current) {
          setReplays(data);
          setLoading(false);
        }
      })
      .catch((error) => {
        console.error("Failed to fetch replays", error);
        if (isMounted.current) {
          setLoading(false);
        }
      });

    return () => {
      isMounted.current = false;
    };
  }, []);

  return { replays, loading };
}

export function useReplayMetadata() {
  const { isReplay } = useReplay();
  const [title, setTitle] = useState<string | null>(null);
  const isLoading = useRef(false);
  const [error, setError] = useState<boolean>(false);
  useEffect(() => {
    if (!isReplay) {
      return;
    }
    if (title || isLoading.current) {
      return;
    }
    isLoading.current = true;
    fetchReplayTitle()
      .then((title) => {
        setError(false);
        setTitle(title ?? null);
        if (title) {
          document.title = `${title} - Deep Research`;
        }
      })
      .catch(() => {
        setError(true);
        setTitle("Error: the replay is not available.");
        document.title = "Deep Research";
      })
      .finally(() => {
        isLoading.current = false;
      });
  }, [isLoading, isReplay, title]);
  return { title, isLoading, hasError: error };
}

export function useConfig(): {
  config: DeerFlowConfig | null;
  loading: boolean;
} {
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState<DeerFlowConfig | null>(null);

  useEffect(() => {
    if (env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY) {
      setLoading(false);
      return;
    }
    fetch(resolveServiceURL("./config"))
      .then((res) => res.json())
      .then((config) => {
        setConfig(config);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch config", err);
        setConfig(null);
        setLoading(false);
      });
  }, []);

  return { config, loading };
}
