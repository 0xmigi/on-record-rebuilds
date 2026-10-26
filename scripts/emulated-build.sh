#!/usr/bin/env bash
# Runs inside a docker container of the other CPU architecture (qemu user
# emulation): SPL Token with that architecture's platform-tools and
# cargo-build-sbf, so the compiler binaries are x86 (or ARM) while the machine
# underneath is not. Usage: emulated-build.sh <tools> <tarball> <cargo-build-sbf or "release:<triple>">
set -euo pipefail
tools=$1 tarball=$2 cbs=$3
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get install -y -qq curl bzip2 git ca-certificates python3 gcc libssl3 libudev1 >/dev/null
uname -m
curl -sSf https://sh.rustup.rs | sh -s -- -y -q --profile minimal --default-toolchain none
export PATH="$HOME/.cargo/bin:$PATH"
if [[ $cbs == release:* ]]; then
  curl -sSfL --retry 3 -o solana.tar.bz2 \
    "https://github.com/anza-xyz/agave/releases/download/v4.1.0/solana-release-${cbs#release:}.tar.bz2"
  tar -xjf solana.tar.bz2 -C /opt && rm solana.tar.bz2
  export PATH="/opt/solana-release/bin:$PATH"
else
  install -m 755 "$cbs" /usr/local/bin/cargo-build-sbf
fi
D="$HOME/.cache/solana/$tools/platform-tools"
mkdir -p "$D" && tar -xjf "$tarball" -C "$D"
git clone -q https://github.com/solana-program/token /src
git -C /src checkout -q 57bd873
cd /src/program
cargo-build-sbf --tools-version "$tools" -- --locked -v 2>&1 | tee /work/out/build.log
cp /src/target/deploy/spl_token.so /work/out/deploy.so
cp /src/target/sbpf-solana-solana/release/spl_token.so /work/out/unstripped.so
python3 /work/tools/scripts/exe-hash.py /work/out/deploy.so | tee /work/out/hash.txt
