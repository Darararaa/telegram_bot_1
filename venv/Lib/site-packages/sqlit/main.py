#!/usr/bin/env python

import argparse
import os
import re
import sqlite3
import sys


def namify(file_name):
    name = os.path.split(os.path.splitext(file_name)[0])[1]
    name = re.sub(r'/[^a-zA-Z0-9]/_/', '_', name)
    return name

def get_table_names(db, master):
    data = db.execute("SELECT name FROM {}.sqlite_master WHERE "
                      "type='table' ORDER BY name".format(master))
    return [row[0] for row in data]

def get_column_names(db, master, name):
    data = db.execute("PRAGMA {}.table_info ({})".format(master, name))
    return [row[1] for row in data]

def main():

    parser = argparse.ArgumentParser(description='Run a quick query on multiple sqlite files.')
    parser.add_argument('-o', '--out', required=False,
                        help='sqlite file to save result in')
    parser.add_argument('-s', '--script', required=False,
                        help='File containing SQL to run')
    parser.add_argument('--sql', required=False,
                        help='SQL to run. This can be added without the --sql if there is '
                        'no ambiguity. '
                        'If no SELECT in query, SELECT is prepended to it. '
                        'If no FROM in query, and first sqlite db has a single table, '
                        'a FROM is added for that table. '
                        'If a second sqlite db also has a single table and one or more '
                        'columns with the same name as the first, a suitable JOIN .. ON '
                        'is added.')
    parser.add_argument('--verbose', action='store_true',
                        help='Show exact sql used.')
    parser.add_argument('--left', action='store_true',
                        help='Prefer left join.')
    parser.add_argument('files', nargs='*')

    args = parser.parse_args()

    sql = None
    if args.script:
        with open(args.script, 'r') as script:
            sql = script.read()

    if args.sql is None and not sql:
        for f in args.files:
            if not os.path.exists(f):
                if args.sql:
                    raise IOError("Sources not found")
                args.sql = f
                args.files.remove(f)

    db_file_name = args.out or ":memory:"
    conn = sqlite3.connect(db_file_name)
    db = conn.cursor()

    output_name = namify(args.out) if args.out else "sheet"

    db.execute("drop table if exists {}".format(output_name))

    db_names = []
    for idx, f in enumerate(args.files):
        name = namify(f)
        db_names.append(name)
        db.execute('attach database ? as ?', [f, name])

    sql = sql or args.sql or "***"

    if "select" not in sql.lower():
        sql = "select {}".format(sql)

    desired = []
    if "from" not in sql.lower():
        prev_db_name = None
        prev_table_name = None
        prev_columns = None
        for idx, db_name in enumerate(db_names):
            names = get_table_names(db, db_name)
            if len(names) > 1:
                break
            table_name = names[0]
            if idx == 0:
                sql = "{} from {}.{}".format(sql, db_name, table_name)
                prev_columns = None
            else:
                if prev_columns is None:
                    prev_columns = get_column_names(db, prev_db_name, prev_table_name)
                    desired += ["{}.{}".format(prev_db_name, c) for c in prev_columns]
                columns = get_column_names(db, db_name, table_name)
                match = set(columns) & set(prev_columns)
                if len(match) > 0:
                    ons = []
                    for c in match:
                        on = "{}.{}.{} = {}.{}.{}".format(
                            prev_db_name, prev_table_name, c,
                            db_name, table_name, c)
                        ons.append(on)
                    sql = "{} {}join {}.{} on {}".format(sql,
                                                         "left " if args.left else "",
                                                         db_name, names[0],
                                                         ' and '.join(ons))
                    for c in columns:
                        if not c in match:
                            desired.append("{}.{}".format(db_name, c))
                else:
                    break
                prev_columns = columns
            prev_db_name = db_name
            prev_table_name = table_name

    if "***" in sql:
        if len(desired) == 0:
            desired.append('*')
        sql = re.sub(r'[*][*][*]', ', '.join(desired), sql)

    if args.verbose:
        print sql

    db.execute("create table {} as {}".format(output_name, sql))

    if not args.out:
        try:
            import unicodecsv as csv
        except ImportError:
            import csv

        data = db.execute("SELECT * FROM {}".format(output_name))
        names = [description[0] for description in data.description]
        writer = csv.writer(sys.stdout)
        writer.writerow(names)
        writer.writerows(data)

    conn.close()

if __name__ == "__main__":
    main()
