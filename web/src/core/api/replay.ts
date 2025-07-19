import type { Replay } from "../messages";

import { resolveServiceURL } from "./resolve-service-url";

export async function queryReplays() {
  const response= await fetch(resolveServiceURL(`replays?limit=100&sort=ts&offset=0`), {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((res) => res.json())
    .then((res) => {
      return res.data? res.data as Array<Replay> : [];
    })
    .catch(() => {
      return [];
    });
  return response;
}

export async function queryReplayById(thread_id: string) {
  const response= await  fetch(resolveServiceURL(`replay/${thread_id}`), {
    method: "GET",
    headers: {
      "Content-Type": "text/plain; charset=UTF-8",
    },
  })
    .then((res) => res.text())
    .then((res) => {
      return res as string;
    })
    .catch(() => {
      return "";
    });
    return response;
}


export async function queryReplayByPath(path: string,options: { abortSignal?: AbortSignal } = {},) {
 
  const response= await fetch(resolveServiceURL(`${path.substring(5)}`), {
    method: "GET",
     headers: {
      "Content-Type": "text/plain; charset=UTF-8",
    },
    signal: options.abortSignal,
  })
    .then((res) => res.text())
    .then((res) => {
      return res as string;
    })
    .catch(() => {
      return `Failed to fetch replay by path: ${path}`;
    });

    return response;
}