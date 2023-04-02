die () {
  echo >&2 "$@"
  exit 1
}

[[ "$#" -eq 1 ] || [ "$#" -eq 2 ] ] || die "1 or 2 arguments required, $# provided"
test -f "/nfs/Linacshare_controlroom/MCR/phoebus_configs/${1}/memento" || die "${1}: file not found"

rm /home/operator-mcr/.phoebus/memento
cp /nfs/Linacshare_controlroom/MCR/phoebus_configs/${1}/memento /home/operator-mcr/.phoebus/memento

if TEST-COMMAND
then
  phoebus
else
  phoebus -settings ${2}
fi
