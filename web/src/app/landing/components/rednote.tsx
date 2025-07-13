import { ChevronRight } from "lucide-react";
import Link from "next/link";

import { AuroraText } from "~/components/magicui/aurora-text";
import { Button } from "~/components/ui/button";
import { env } from "~/env";

export function Rednote() {
  return (
    <section className="flex h-[35vh] w-full flex-col items-center justify-center pb-1">
       
      <div className="relative z-10 flex flex-col items-center justify-center gap-2">
        <h1 className="text-center text-3xl font-bold md:text-3xl">
          <span className="bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
            Sky Creative Assistant{" "}
          </span>
          
          <AuroraText>with deep research</AuroraText>
        </h1>

        <p className="max-w-4xl p-0 text-center text-sm opacity-85 md:text-xl">
          Multi-agent system and MCP tools using NVIDIA NIM and Langchain for @SkyHackthon 12th.
        </p>

        <div className="flex gap-6">
          
          <Button className="hidden text-lg md:flex md:w-42" size="lg" asChild>
            <Link
              target={env.NEXT_PUBLIC_STATIC_WEBSITE_ONLY ? "_blank" : undefined}
              href={ "/chat"}
            >
              Get Started <ChevronRight />
            </Link>
          </Button>
          
        </div>
      </div>
     
    </section>
  );
}
