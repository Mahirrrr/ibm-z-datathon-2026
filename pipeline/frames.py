"""Read and write pipeline tables as Arrow IPC (Feather) files.

Why not Parquet: the only pyarrow build for s390x (conda defaults, 19.0.0) reads numeric
Parquet columns back as nulls on big-endian. Arrow IPC round-trips correctly there and
byte-swaps little-endian files on read, so the same files move between the Mac and LinuxONE.
"""

import pandas as pd
import pyarrow as pa
import pyarrow.feather as feather

COMPRESSION = "zstd"


def write(df, path):
    feather.write_feather(pa.Table.from_pandas(df, preserve_index=False), path, compression=COMPRESSION)


def read(path, columns=None, where=None):
    """Load columns into pandas. `where` names a boolean column; only rows where it is true are
    converted, which keeps the 26M-row files inside the LinuxONE VM's 8 GB."""
    wanted = None if columns is None else list(dict.fromkeys(columns + ([where] if where else [])))
    table = feather.read_table(path, columns=wanted)
    if where:
        table = table.filter(table[where].fill_null(False))
        if columns is not None and where not in columns:
            table = table.drop_columns([where])
    return table.to_pandas()
