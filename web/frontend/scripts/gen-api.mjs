#!/usr/bin/env node
// Generates src/api/schema.d.ts from the committed OpenAPI snapshot.
//
// Offline by default: reads ./openapi.json (a committed snapshot of the
// FastAPI spec). Override with a live/other spec via the OPENAPI_URL env var:
//
//   OPENAPI_URL=http://10.8.0.15:3000/openapi.json bun run gen:api
//
import { readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

import openapiTS, { astToString } from 'openapi-typescript'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const snapshot = resolve(root, 'openapi.json')
const outFile = resolve(root, 'src/api/schema.d.ts')

const override = process.env.OPENAPI_URL?.trim()
const source = override && override.length > 0 ? override : snapshot

const input = /^https?:\/\//i.test(source)
  ? new URL(source)
  : JSON.parse(await readFile(resolve(root, source), 'utf8'))

console.log(`[gen:api] ${override ? 'OPENAPI_URL override' : 'snapshot'}: ${source}`)
const ast = await openapiTS(input)
await writeFile(outFile, astToString(ast), 'utf8')
console.log(`[gen:api] wrote ${outFile}`)
