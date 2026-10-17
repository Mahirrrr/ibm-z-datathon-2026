"""Read only the needed columns from the 760 MB OpenFEMA parquet, one row group at a time,
and write a slim working table. Peak memory stays at one row group plus the output.
"""

import time

import pyarrow as pa
import pyarrow.parquet as pq

from pipeline.config import IHP_RAW, IHP_SLIM, MONEY_COLUMNS, PROCESSED_DIR, SLIM_COLUMNS


def slim_table(table):
    """Cast decimal money columns to float32; leave everything else as-is."""
    for name in MONEY_COLUMNS:
        if name in table.column_names:
            idx = table.column_names.index(name)
            table = table.set_column(idx, name, table[name].cast(pa.float32()))
    return table


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    source = pq.ParquetFile(IHP_RAW)
    start = time.perf_counter()
    writer = None
    try:
        for i in range(source.num_row_groups):
            table = slim_table(source.read_row_group(i, columns=SLIM_COLUMNS))
            if writer is None:
                writer = pq.ParquetWriter(IHP_SLIM, table.schema, compression="zstd")
            writer.write_table(table)
    finally:
        if writer is not None:
            writer.close()
    elapsed = time.perf_counter() - start
    rows = source.metadata.num_rows
    print(f"wrote {rows:,} rows x {len(SLIM_COLUMNS)} cols to {IHP_SLIM} in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
