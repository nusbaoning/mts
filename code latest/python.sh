#!/bin/bash

l=(
web_2
usr_20
)
len=(
0.04
0.06
0.08
0.12
0.14
0.16
)

for str in ${l[@]}; do
	# nohup python3 mts_alg_core.py "$str" "cam" &
	for num in ${len[@]}; do
		echo $str 
		echo $num
		nohup python3 mts_alg_core.py "$str" "cam" "$num"&
	done	
done
