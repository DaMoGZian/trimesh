# exit if anything fails
set -xe

apt-get update
PACKAGES_BUILD="git ca-certificates build-essential g++ gcc cmake"
apt-get -y --no-install-recommends install $PACKAGES_BUILD

# install draco, google's mesh compression utility
bash "$(dirname $0)/draco.bash"
# install VHACD, a mesh decomposition utility
bash "$(dirname $0)/vhacd.bash"

# remove garbage
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*



