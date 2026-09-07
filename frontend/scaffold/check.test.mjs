import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
test('foundation typecheck covers a real TypeScript input', () => {
  const config=JSON.parse(readFileSync(new URL('../tsconfig.json', import.meta.url)));
  assert.equal(config.compilerOptions.strict,true);
  assert.deepEqual(config.include,['scaffold/**/*.ts']);
  const source=readFileSync(new URL('./foundation.ts', import.meta.url),'utf8');
  assert.match(source,/NOT_IMPLEMENTED/);
});
