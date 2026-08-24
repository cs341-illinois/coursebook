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
# site_deploy.sh pushes an empty commit to the website repo to trigger a
# rebuild there. That needs the SITE_DEPLOY_KEY deploy key, which the
# workflow writes to /tmp/deploy_site. Skip rather than fail when it is
# absent, so forks and any run without the secret still succeed.
if [ -f /tmp/deploy_site ]; then
    bash _scripts/site_deploy.sh
else
    echo "Skipping site deploy: /tmp/deploy_site is not present"
fi
