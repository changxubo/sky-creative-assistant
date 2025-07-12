

import { Settings, type LucideIcon } from "lucide-react";

import { GeneralTab } from "./general-tab";
import { MCPTab } from "./mcp-tab";

export const SETTINGS_TABS = [GeneralTab, MCPTab].map((tab) => {
  const name = tab.displayName ?? tab.name;
  return {
    ...tab,
    id: name.replace(/Tab$/, "").toLocaleLowerCase(),
    label: name.replace(/Tab$/, ""),
    icon: (tab.icon ?? <Settings />) as LucideIcon,
    component: tab,
  };
});
