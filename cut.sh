#!/bin/bash

l=(
prxy_1
# usr_1
# usr_2
)
# path=/mnt/raid5/trace/MS-Cambridge/
for str in ${l[@]}; do
	dd if=$str.csv.req of=temp.csv.req bs=1M count=500
	filename=${str}"0.csv.req"
	echo $filename
	cat temp.csv.req | head -n -1 > $filename
	rm temp.csv.req
done
