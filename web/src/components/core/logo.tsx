import Link from "next/link";

import { AuroraText } from "~/components/magicui/aurora-text";

export function Logo() {
  return (
      <Link
      className="text-2xl md:text-4xl sm:text-3xl font-bold opacity-70 transition-opacity duration-300 hover:opacity-100"
      href="/"
    >
     <AuroraText>Amway Creative Assistant</AuroraText>
    </Link> 
  );
}
