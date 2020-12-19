# Error handling
if [[ $# -ne 4 ]]
then
  echo "4 parameters expected:"
  echo "- \$1 => server (.py)"
  echo "- \$2 => inspector (.py)"
  echo "- \$3 => fantom (.py)"
  echo "- \$4 => Nb of tests"
  exit 2
fi

count=$4
fantom_wins=0

for i in $(seq $count)
do
  py $1 > test_logs 2>&1 &
  pid=$!

  py $2 > /dev/null 2>&1 &

  py $3 > /dev/null 2>&1 &
  wait $pid
  output=$( cat test_logs )
  if [[ $output =~ "fantom wins" ]]
  then
    # echo "$i: Fantom wins"
    ((fantom_wins=fantom_wins+1))
  # else
  #   echo "$i: Inspector wins"
  fi
done

rm test_logs
inspector_wins=$((count-fantom_wins))
echo
echo "Fantom won ${fantom_wins} times"
echo "Inspector won ${inspector_wins} times"
