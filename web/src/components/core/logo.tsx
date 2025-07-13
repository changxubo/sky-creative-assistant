import Link from "next/link";

import { AuroraText } from "~/components/magicui/aurora-text";

export function Logo() {
  return (
      <Link
      className="opacity-70 transition-opacity duration-300 hover:opacity-100"
      href="/"
    >
     <AuroraText>Sky Creative Assistant</AuroraText>
    </Link> 
  );
}
