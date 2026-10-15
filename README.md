# on-record-rebuilds

Rebuilds Solana programs from their public source, on the kind of machine they
were built on, and compares the result with the bytes deployed on mainnet. No
Docker image: each build runs on a fresh GitHub-hosted machine (Linux,
Apple-silicon Mac or Intel Mac) with the program's own Solana tool and compiler
(platform-tools) versions. Every run's logs are public.

Run: Actions → rebuild → Run workflow, with a batch file from `batches/`.
