import * as duckdb from '@duckdb/duckdb-wasm';
import eh_worker from '@duckdb/duckdb-wasm/dist/duckdb-browser-eh.worker.js?url';
import mvp_worker from '@duckdb/duckdb-wasm/dist/duckdb-browser-mvp.worker.js?url';
import duckdb_wasm_eh from '@duckdb/duckdb-wasm/dist/duckdb-eh.wasm?url';
import duckdb_wasm from '@duckdb/duckdb-wasm/dist/duckdb-mvp.wasm?url';
import { PARQUET_URL, PARQUET_VIRTUAL_NAME } from './constants';

const MANUAL_BUNDLES: duckdb.DuckDBBundles = {
  mvp: {
    mainModule: duckdb_wasm,
    mainWorker: mvp_worker,
  },
  eh: {
    mainModule: duckdb_wasm_eh,
    mainWorker: eh_worker,
  },
};

export interface DuckDbContext {
  db: duckdb.AsyncDuckDB;
  conn: duckdb.AsyncDuckDBConnection;
}

let initPromise: Promise<DuckDbContext> | null = null;

/**
 * ブラウザ内 DuckDB-Wasm を初期化し、Hugging Face 上の Parquet を仮想テーブルとしてマウントする。
 * 同時呼び出しは単一の初期化 Promise でデデュープする。
 */
export async function getDuckDb(): Promise<DuckDbContext> {
  if (initPromise) {
    return initPromise;
  }

  initPromise = (async () => {
    const bundle = await duckdb.selectBundle(MANUAL_BUNDLES);
    if (!bundle.mainWorker) {
      throw new Error('DuckDB-Wasm worker bundle could not be resolved.');
    }

    const worker = new Worker(bundle.mainWorker);
    const logger = new duckdb.ConsoleLogger(duckdb.LogLevel.WARNING);
    const db = new duckdb.AsyncDuckDB(logger, worker);

    await db.instantiate(bundle.mainModule, bundle.pthreadWorker);
    await db.open({
      query: {
        castBigIntToDouble: true,
      },
    });

    await db.registerFileURL(
      PARQUET_VIRTUAL_NAME,
      PARQUET_URL,
      duckdb.DuckDBDataProtocol.HTTP,
      false,
    );

    const conn = await db.connect();
    await conn.query(
      `CREATE OR REPLACE VIEW laws_articles AS SELECT * FROM read_parquet('${PARQUET_VIRTUAL_NAME}')`,
    );

    return { db, conn };
  })().catch((err) => {
    initPromise = null;
    throw err;
  });

  return initPromise;
}
