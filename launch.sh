die () {
  echo >&2 "$@"
  exit 1
}

[ "$#" -eq 1 ] || die "1 argument required, $# provided"
test -f "/nfs/Linacshare_controlroom/MCR/phoebus_configs/${1}/memento" || die "${1}: file not found"

rm /home/operator-mcr/.phoebus/memento
cp /nfs/Linacshare_controlroom/MCR/phoebus_configs/${1}/memento /home/operator-mcr/.phoebus/memento
phoebus
