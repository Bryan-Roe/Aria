// Define a minimal tag function named `$` so TypeScript knows this identifier
// and the tagged template below becomes valid instead of causing `Cannot find name '$'`.
export function $(strings: TemplateStringsArray, ...values: unknown[]): string {
	return strings.reduce((acc, s, i) => acc + s + (i < values.length ? String(values[i]) : ""), "");
}

// A short poem in code:
export default $`Lines like loops,
	variables of breeze;
	semicolons keep their rhythm,
	and my heart logs ease.
`;
