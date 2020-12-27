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
inspector_wins=0

for i in $(seq $count)
do
  python $1 > test_logs 2>&1 &
  pid=$!
  python $2 > toto 2>&1 &
  python $3 > tata 2>&1 &
  wait $pid
  output=$( cat test_logs )
  if [[ $output =~ "fantom wins" ]]
  then
    echo "$i: Fantom wins"
    ((fantom_wins=fantom_wins+1))
  elif [[ $output =~ "inspector wins" ]]
  then
    echo "$i: Inspector wins"
    ((inspector_wins=inspector_wins+1))
  else
    echo "$i: Error"
  fi
done

#rm test_logs
echo
echo "Fantom won ${fantom_wins} times"
echo "Inspector won ${inspector_wins} times"