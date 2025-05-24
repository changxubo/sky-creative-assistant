// Copyright (c) 2025 Rednote Creative Assistant
// SPDX-License-Identifier: MIT

import Link from "next/link";

export function Logo() {
  return (
    <Link
      className="opacity-70 transition-opacity duration-300 hover:opacity-100 text-xl font-medium "
      href="/"
    >
      {/*🦌 Rednote Creative Assistant*/}
     <span style={{ paddingLeft: "30px" }}>Rednote Creative Assistant</span>
    </Link>
  );
}
