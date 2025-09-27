# CLI Usage

The `glazing` command provides access to all functionality from the terminal.

## Quick Reference

```bash
glazing init                    # Download and set up all datasets
glazing search query "give"     # Search across datasets
glazing search entity give.01   # Look up specific entity
glazing download list           # Show available datasets
```

## Initialization

The first step is always `glazing init`, which downloads and prepares all datasets. You can specify a custom location:

```bash
glazing init --data-dir /my/data/path
```

Or use an environment variable:

```bash
export GLAZING_DATA_DIR=/my/data/path
glazing init
```

## Searching

The search command is the main way to explore the data. Search by text query:

```bash
glazing search query "abandon"
glazing search query "run" --dataset verbnet
glazing search query "give" --limit 10 --json
```

Look up specific entities by their IDs:

```bash
glazing search entity give-13.1 --dataset verbnet
glazing search entity 01772306 --dataset wordnet
```

Find cross-references between datasets:

```bash
glazing search cross-ref --source propbank --id "give.01" --target verbnet
glazing search cross-ref --source verbnet --id "give-13.1" --target all
```

## Downloading and Converting

If you need to work with individual datasets or update them:

```bash
glazing download dataset --dataset verbnet
glazing convert dataset --dataset verbnet --input-dir raw --output-dir converted
```

To see what's available:

```bash
glazing download list
glazing download info verbnet
```

## Output Formats

By default, output is formatted for human reading. Add `--json` for programmatic use:

```bash
glazing search query "give" --json | jq '.results[0]'
```

## Troubleshooting

If searches return no results, check that initialization completed:

```bash
ls ~/.local/share/glazing/converted/
```

For permission issues, use a different directory:

```bash
glazing init --data-dir ~/my-data
export GLAZING_DATA_DIR=~/my-data
```

Memory issues with large datasets can be avoided by processing them individually rather than using `--dataset all`.

## Environment Variables

- `GLAZING_DATA_DIR`: Where to store/find data (default: `~/.local/share/glazing`)
- `GLAZING_SKIP_INIT_CHECK`: Skip the initialization warning when importing the package
- `XDG_DATA_HOME`: Alternative base directory on Linux/macOS
