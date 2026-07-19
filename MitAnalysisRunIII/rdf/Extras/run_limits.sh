#!/bin/sh

for op in T0 T1 T2 S0 M0 M1 M7
do
    root -l -q "plotlimits.C(\"${op}\")"
done
