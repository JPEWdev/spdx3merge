# Merge SPDX 3 Document

A tool to merge SPDX 3 Documents

## Installation

`spdx3merge` can be installed using `pip`:

```shell
python3 -m pip install spdx3merge
```

## Usage

In a basic form, `spdx3merge` will merge multiple input documents into a single
output document. To specify the input documents, use the `--input` or `-i`
arguments. The output document is specified with `--output` or `-o`.

The first input document specified is considered the "root" document; that is
all of its root elements will be copied to the output document root elements.

In order to generate proper output document, at least one `--author-` argument
must be specified. The easiest is to use `--author-person` and specify your
name. For other author options, see `spdx3merge --help`.

Here is a complete example:

```shell
spdx3merge \
    --input A.spdx.json \
    --input B.spdx.json \
    --input C.spdx.json \
    --output out.spdx.json \
    --author-person "Joshua Watt"
```

If you are going to read the document, you'll most likely also want the
`--pretty` option to make it more readable

## Development

Development on `spdx3merge` can be done by setting up a virtual environment and
installing it in editable mode:

```shell
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

Tests can be run using pytest:

```shell
pytest -v
```
