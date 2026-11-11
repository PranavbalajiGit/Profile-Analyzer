export function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function humanizeAction(action: string): string {
  return action
    .replace(/[._]/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function shortId(value: string | null): string {
  return value ? value.slice(0, 8) : "—";
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong.";
}
