#!/bin/bash

set -e;

# Set up ssh. IdentitiesOnly stops ssh offering any other key it finds.
git config --global core.sshCommand "ssh -i /tmp/deploy_site -o IdentitiesOnly=yes -F /dev/null"
export DOCS_SHA=$(git rev-parse --short HEAD)

# Clone the site repo. The empty commit below is what triggers its
# Website Deploy workflow, which pulls the coursebook wiki via the
# _coursebook submodule and republishes.
git clone -b develop --depth 1 git@github.com:cs341-illinois/cs341-illinois.github.io.git ${CLONE_DIR}
cd ${CLONE_DIR}

# The site reads the coursebook through the _coursebook submodule, and its
# workflow updates that with --remote, so the build always takes the wiki's
# latest commit and the SHA recorded in the tree is ignored. Leaving that
# SHA to rot is still a trap: anyone running a plain 'git submodule update'
# builds a months-old book. Point it at the wiki commit push_to_wiki.sh
# just published, so the recorded pointer matches what actually deploys.
#
# ls-remote means we never fetch the submodule: a gitlink is just an index
# entry, so update-index can write it directly into this shallow clone.
# Both steps are non-fatal on purpose. This script runs under 'set -e' and
# its real job is the push below, which is what rebuilds the site; a
# transient ls-remote failure must not cost us the rebuild.
WIKI_SHA=$(git ls-remote "https://github.com/${GITHUB_REPOSITORY}.wiki.git" refs/heads/master | cut -f1) || true
if [ -n "${WIKI_SHA}" ]; then
    git update-index --add --cacheinfo "160000,${WIKI_SHA},_coursebook" \
        || echo "Could not write the submodule pointer; pushing without the bump"
else
    echo "Could not resolve the wiki head; leaving the submodule pointer alone"
fi

# --allow-empty because the pointer is often already current -- there is
# nothing to commit then, but the push still has to happen: it is the empty
# commit that triggers the site's Website Deploy workflow.
git commit --allow-empty -m "Updating docs to ${DOCS_SHA}"
git push origin develop

# Go back to the build dir
cd ${GITHUB_WORKSPACE}
