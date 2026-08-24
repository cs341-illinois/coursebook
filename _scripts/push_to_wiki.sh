#!/bin/bash

# Every script should have this
set -e

DOCS_SHA=$(git rev-parse --short HEAD)

# Create a temp directory, so we don't get raced by the filesystem
WIKI_DIR=`mktemp -d`

# Push over https with the built-in GITHUB_TOKEN instead of the retired
# deploy key. Echo the ssh form so the token never reaches the log.
CLONE_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.wiki.git"
echo "Cloning ${GITHUB_REPOSITORY}.wiki into $WIKI_DIR"
# git config --global core.sshCommand "ssh -i /tmp/deploy_wiki -F /dev/null"
git clone $CLONE_URL $WIKI_DIR

# If we get race condition on read only files, we need to fix our build system
# no temp directory here

echo "Copying Wiki"
cp _wiki/* ${WIKI_DIR}

cd ${WIKI_DIR}

git add -A
git commit -m "Updating wiki to ${DOCS_SHA}" --author "$COMMITTER_EMAIL <$AUTHOR_NAME>" || true
git push origin

cd ${GITHUB_WORKSPACE}


# Part 2, Update the site
#
# Disabled. site_deploy.sh pushes an empty commit to a DIFFERENT repo to
# nudge the website into rebuilding, and the built-in GITHUB_TOKEN is
# scoped to this repo only, so it cannot do that. Re-enabling it needs a
# PAT (or a deploy key) in a secret.
#
# It also still names illinois-cs241/illinois-cs241.github.io, which is
# two renames stale - the site now lives at
# cs341-illinois/cs341-illinois.github.io - so that URL needs updating
# before this is switched back on.
# bash _scripts/site_deploy.sh
