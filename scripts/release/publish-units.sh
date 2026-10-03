#!/usr/bin/env bash
# Build released package units for PyPI, at every stage of a train. publish.yml calls it and then
# uploads what it built with pypa/gh-action-pypi-publish; release-please.yml dispatches publish.yml
# with the released paths and the train's stage.
#
# The registry follows from the file the unit carries (unit_registry). Every unit of this repo is a
# Python package (pyproject.toml), and publish.yml installs only uv, so a unit with any other file
# stops the run. release-please writes the SemVer version as is (1.1.0-alpha.1); the build backend
# normalizes it to PEP 440 (1.1.0a1), and the version checked against PyPI is read back from the
# built wheel's filename, not converted here. PyPI has no dist-tags: pip skips pre-releases unless asked (--pre).
#
# Every unit's version must belong to <stage> (version_stage in scripts/lib/release-stages.sh), so a
# dispatch with the wrong stage stops. A path must be an entry of the manifest, which lists exactly
# this repo's two packages, so nothing else is built. A version that is already on PyPI is left out
# of the upload directory, so a re-run is safe.
#
# usage: publish-units.sh <alpha|beta|rc|ga> <path>...
#   PUBLISH_OUT  where packages are built (default tmp/publish): the upload directory is pypi/, which
#                holds nothing but the wheels and sdists to upload, because the upload checks every
#                file in it.
# Under GitHub Actions it writes count=<files to upload> and dir=<upload directory> to $GITHUB_OUTPUT.
set -euo pipefail
source "$(dirname "$0")/../lib/common.sh"
cd "$REPO_ROOT"
usage() { die "usage: publish-units.sh <alpha|beta|rc|ga> <path>..."; }

toml_get() { # toml_get <file> <table> <key>
  python3 -c 'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb"))[sys.argv[2]][sys.argv[3]])' "$@"
}

summary() { [[ -z "${GITHUB_STEP_SUMMARY:-}" ]] || printf '%s\n' "- $*" >> "$GITHUB_STEP_SUMMARY"; }

# The unit's own file must carry the manifest version: release-please writes both in one commit, and
# a broken updater would otherwise publish a version the manifest never released.
check_file_version() { # check_file_version <path> <file> <version in file> <manifest version>
  [[ "$3" == "$4" ]] || die "$1：manifest 是 $4，但 $2 是 ${3:-（空）}；release-please 沒有更新到這個檔"
}

build_pypi() { # build_pypi <path> <version>
  local p="$1" ver="$2" name build out pyver
  local -a wheels
  name="$(toml_get "$p/pyproject.toml" project name)"
  check_file_version "$p" "$p/pyproject.toml" "$(toml_get "$p/pyproject.toml" project version)" "$ver"
  build="$PUBLISH_OUT/build/${p##*/}" out="$PUBLISH_OUT/pypi"
  rm -rf "$build"; mkdir -p "$build" "$out"
  uv build --quiet --sdist --wheel --out-dir "$build" "$p"
  # The wheel filename carries the normalized version (name-1.1.0a1-py3-none-any.whl; a "-" inside
  # the name is escaped to "_"). The METADATA inside may keep the raw 1.1.0-alpha.1, so it is not read.
  wheels=("$build"/*.whl)
  (( ${#wheels[@]} == 1 )) || die "$p 應建出 1 份 wheel，實際 ${#wheels[@]} 份"
  pyver="$(cut -d- -f2 <<<"${wheels[0]##*/}")"
  if curl -fsS -o /dev/null "https://pypi.org/pypi/$name/$pyver/json" 2>/dev/null; then
    info "PyPI：$name $pyver 已發布，略過"
    summary "PyPI \`${name} ${pyver}\` 已在註冊中心，略過"
    return 0
  fi
  mv "$build"/* "$out"/
  log "PyPI：${name} ${ver} → ${pyver}（PEP 440，取自建置出的 wheel 檔名）"
  summary "PyPI \`${name} ${pyver}\`（版號 ${ver}）"
}

# publish.yml runs at the tag release-please.yml dispatched it with: the tag of the first path, which is
# <component>/v<version> (include-component-in-tag, tag-separator "/"). Any other ref, such as a branch
# or an older tag, would publish a version the ref does not carry, so stop. A local run is not checked.
check_dispatch_ref() { # check_dispatch_ref <first path>
  [[ "${GITHUB_ACTIONS:-}" == true ]] || return 0
  local p="${1%/}" comp ver want
  comp="$(jq -r --arg p "$p" '.packages[$p].component // empty' "$CONFIG")"
  ver="$(manifest_version "$p")"
  [[ -n "$comp" && -n "$ver" ]] || die "$p 在 ${CONFIG} 沒有 component，或在 ${MANIFEST} 沒有版號，無法核對發布的 tag"
  want="refs/tags/$comp/v$ver"
  [[ "${GITHUB_REF:-}" == "$want" ]] || die "發布必須從 tag ${want#refs/tags/} 執行，但 GITHUB_REF 是「${GITHUB_REF:-（空）}」"
}

[[ $# -ge 2 ]] || usage
stage="$1"; shift
check_dispatch_ref "$1"
is_stage "$stage" || die "階段「${stage}」不是 ${RELEASE_STAGES[*]} 之一"
PUBLISH_OUT="${PUBLISH_OUT:-$REPO_ROOT/tmp/publish}"
rm -rf "$PUBLISH_OUT/build" "$PUBLISH_OUT/pypi"
mkdir -p "$PUBLISH_OUT/pypi"
for p in "$@"; do
  p="${p%/}"
  ver="$(manifest_version "$p")"
  [[ -n "$ver" ]] || die "$p 不在 ${MANIFEST}，不是本倉庫發布的套件"
  vs="$(version_stage "$ver")" || die "$p 的版號 $ver 不是 X.Y.Z 或 X.Y.Z-<alpha|beta|rc>.N，無法決定發布階段"
  [[ "$vs" == "$stage" ]] || die "$p 的版號 $ver 屬於 ${vs}，但這次發布的階段是 ${stage}"
  reg="$(unit_registry "$p")" || die "$p 沒有 pyproject.toml，不知道要發布到哪個註冊中心"
  [[ "$reg" == pypi ]] || die "$p 的單元檔對應 ${reg}，本倉庫的 publish.yml 只發布到 PyPI"
  build_pypi "$p" "$ver"
done
count="$(find "$PUBLISH_OUT/pypi" -type f | wc -l | tr -d ' ')"
log "PyPI：待上傳 ${count} 個檔"
find "$PUBLISH_OUT/pypi" -type f -exec basename {} \; | sort | sed 's/^/  /'
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  printf '%s\n' "count=$count" "dir=$PUBLISH_OUT/pypi" >> "$GITHUB_OUTPUT"
fi
