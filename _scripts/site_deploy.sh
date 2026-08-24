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

git commit --allow-empty -m "Updating docs to ${DOCS_SHA}"
git push origin develop

# Go back to the build dir
cd ${GITHUB_WORKSPACE}
