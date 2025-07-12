

import { BadgeInfo } from "lucide-react";

import { Markdown } from "~/components/core/markdown";

import about from "./about.md";
import type { Tab } from "./types";

export const AboutTab: Tab = () => {
  return <Markdown>{about}</Markdown>;
};
AboutTab.icon = BadgeInfo;
AboutTab.displayName = "About";
