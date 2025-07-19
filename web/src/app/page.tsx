import { Rednote } from "./landing/components/rednote";
import { MultiAgentSection } from "./landing/sections/multi-agent-section";
import {ReplaysSection} from "./landing/components/replays";
/**
 * Home page component that renders the main landing page
 * with hero section and multi-agent architecture visualization
 */
export default function HomePage() {
  return (
    <div className="flex flex-col items-center">
      <main className="container flex flex-col items-center justify-center gap-0">
        <Rednote />
        <ReplaysSection />
        <MultiAgentSection />
      </main>
    </div>
  );
}

