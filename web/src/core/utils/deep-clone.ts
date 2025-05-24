// Copyright (c) 2025 Rednote Creative Assistant
// SPDX-License-Identifier: MIT

export function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value));
}
