die () {
  echo >&2 "$@"
  exit 1
}

[[ "$#" -eq 1 ]] || [[ "$#" -eq 2 ]] || die "1 or 2 arguments required, $# provided"
test -f "/usr/local/share/cs-studio/layouts/${1}" || die "${1}: file not found"

rm /home/operator-mcr/.phoebus/memento
cp /usr/local/share/cs-studio/layouts/${1} /home/operator-mcr/.phoebus/memento

if [ "$#" -eq 1 ]
then
  phoebus -server 1234
else
  phoebus -server 1234 -settings ${2}
fi
