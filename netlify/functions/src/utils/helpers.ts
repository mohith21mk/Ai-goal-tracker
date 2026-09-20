export function toInt(val: any, defaultVal = 0): number {
  if (val === undefined || val === null) return defaultVal;
  const str = Array.isArray(val) ? val[0] : String(val);
  const n = parseInt(str, 10);
  return isNaN(n) ? defaultVal : n;
}

export function toStr(val: any, defaultVal = ''): string {
  if (val === undefined || val === null) return defaultVal;
  return Array.isArray(val) ? String(val[0]) : String(val);
}
