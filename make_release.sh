#!/bin/bash

# fail on error
set -e

# confirm the supplied version bump is valid
version_bump=$1

case $version_bump in
  "patch" | "minor" | "major" | "rc" | "dev" | "alpha" | "beta" | "release" | "post")
    echo "valid version bump: $version_bump"
    ;;
  *)
    echo "invalid version bump: \"$version_bump\""
    echo "Usage:"
    echo ""
    echo "    bash make_release.sh <version bump>"
    echo ""
    echo "List of valid version bumps: patch, minor, major, prepatch, preminor, premajor, prerelease"
    exit 1
    ;;
esac

if [ -n "$(git status --untracked-files=no --porcelain)" ]; then
  echo "The repository has uncommitted changes."
  echo "This will lead to problems with git checkout."
  exit 2
fi

if [ $(git symbolic-ref --short -q HEAD) != "main" ]; then
  echo "not on main branch"
  exit 3
fi

echo ""
echo "######################################"
echo "# ensure main branch is up-to-date  #"
echo "######################################"
git pull

bump_build_publish() {
  echo "#######################################"
  echo "#           entering '$1'             #"
  echo "#######################################"
  pushd $1

  echo "#######################################"
  echo "#            bump version             #"
  echo "#######################################"
  hatch version $version_bump

  echo "#######################################"
  echo "#         stage pyroject.toml         #"
  echo "#######################################"
  git add pyproject.toml

  echo "#######################################"
  echo "#            do new build             #"
  echo "#######################################"
  rm -rf build dist
  hatch build

  echo ""
  echo "#######################################"
  echo "#          publish package            #"
  echo "#######################################"
  # to use this, set up an API token with
  #  `poetry config pypi-token.pypi <api token>`
  hatch publish

  echo "#######################################"
  echo "#            leaving '$1'             #"
  echo "#######################################"
  popd  # switch back to previous directory
}

cp README.md ./type-enum/
bump_build_publish "type-enum"
rm ./type-enum/README.md
bump_build_publish "type-enum-plugin"

# get the version from 'type_enum'
pushd type-enum
new_version=v$(hatch version)
popd

echo "#######################################"
echo "#         create new branch           #"
echo "#######################################"
branch_name=release-$new_version
git checkout -b $branch_name

echo "#######################################"
echo "#       commit version change         #"
echo "#######################################"
git commit -m "Bump version"

echo "#######################################"
echo "#          new tag: $new_tag          #"
echo "#######################################"
new_tag=v${new_version}
git tag $new_tag

bump_to_prerelease() {
  echo "#######################################"
  echo "#           entering '$1'             #"
  echo "#######################################"
  pushd $1

  echo "#######################################"
  echo "#      bump prerelease version        #"
  echo "#######################################"
  hatch version dev

  echo "#######################################"
  echo "#       commit version change         #"
  echo "#######################################"
  git add pyproject.toml

  echo "#######################################"
  echo "#            leaving '$1'             #"
  echo "#######################################"
  popd  # switch back to previous directory
}
bump_to_prerelease "type-enum"
bump_to_prerelease "type-enum-plugin"

git commit -m "Bump version to prerelease"

echo "#######################################"
echo "#       commit version change         #"
echo "#######################################"
git push origin $branch_name $new_tag

echo "#######################################"
echo "#     create PR for version bump      #"
echo "#######################################"
gh pr create --title "Version bump $new_tag" --body "__Do not use squash merge__ !" --base "main" --label version-bump
# the following command is allowed to fail; hence the "||:" at the end
gh pr merge $branch_name --merge --admin || :

echo "#######################################"
echo "#           create release            #"
echo "#######################################"
gh release create $new_tag --generate-notes

# clean up
echo "#######################################"
echo "#      go back to main branch         #"
echo "#######################################"
git checkout main
