#!/bin/bash
#root -l -b -q 'checkEFTshapes.C("operator",value of c'() where c' =1/c, original value of coeff, variable number)'
# e.x if we need to scale it to 10 and the initial value is 2 then, 10=2/c' so c' = 2/10 = 0.2

mkdir -p plots

root -l -b -q 'checkEFTshapes.C("T2",2.0, 2.0, 99, 38, 39)'
root -l -b -q 'checkEFTshapes.C("T2",1.0, 2.0, 99, 38, 39)'
root -l -b -q 'checkEFTshapes.C("T2",0.2, 2.0, 99, 38, 39)'

root -l -b -q 'checkEFTshapes.C("T2",2.0, 2.0, 24, 38, 39)'
root -l -b -q 'checkEFTshapes.C("T2",1.0, 2.0, 24, 38, 39)'
root -l -b -q 'checkEFTshapes.C("T2",0.2, 2.0, 24, 38, 39)'

root -l -b -q 'checkEFTshapes.C("T2",2.0, 2.0, 115, 38, 39)'
root -l -b -q 'checkEFTshapes.C("T2",1.0, 2.0, 115, 38, 39)'
root -l -b -q 'checkEFTshapes.C("T2",0.2, 2.0, 115, 38, 39)'


root -l -b -q 'checkEFTshapes.C("T0",2.0, 2.0, 99, 34, 35)'
root -l -b -q 'checkEFTshapes.C("T0",1.0, 2.0, 99, 34, 35)'
root -l -b -q 'checkEFTshapes.C("T0",0.2, 2.0, 99, 34, 35)'

root -l -b -q 'checkEFTshapes.C("T0",2.0, 2.0, 24, 34, 35)'
root -l -b -q 'checkEFTshapes.C("T0",1.0, 2.0, 24, 34, 35)'
root -l -b -q 'checkEFTshapes.C("T0",0.2, 2.0, 24, 34, 35)'

root -l -b -q 'checkEFTshapes.C("T0",2.0, 2.0, 115, 34, 35)'
root -l -b -q 'checkEFTshapes.C("T0",1.0, 2.0, 115, 34, 35)'
root -l -b -q 'checkEFTshapes.C("T0",0.2, 2.0, 115, 34, 35)'


root -l -b -q 'checkEFTshapes.C("T1",2.0, 1.0, 99, 36, 37)'
root -l -b -q 'checkEFTshapes.C("T1",1.0, 1.0, 99, 36, 37)'
root -l -b -q 'checkEFTshapes.C("T1",0.1, 1.0, 99, 36, 37)'

root -l -b -q 'checkEFTshapes.C("T1",2.0, 1.0, 24, 36, 37)'
root -l -b -q 'checkEFTshapes.C("T1",1.0, 1.0, 24, 36, 37)'
root -l -b -q 'checkEFTshapes.C("T1",0.1, 1.0, 24, 36, 37)'

root -l -b -q 'checkEFTshapes.C("T1",2.0, 1.0, 115, 36, 37)'
root -l -b -q 'checkEFTshapes.C("T1",1.0, 1.0, 115, 36, 37)'
root -l -b -q 'checkEFTshapes.C("T1",0.1, 1.0, 115, 36, 37)'



root -l -b -q 'checkEFTshapes.C("S0",15.0, 15.0, 99, 32, 33)'
root -l -b -q 'checkEFTshapes.C("S0",1.0, 15.0, 99, 32, 33)'
root -l -b -q 'checkEFTshapes.C("S0",1.5, 15.0, 99, 32, 33)'

root -l -b -q 'checkEFTshapes.C("S0",15.0, 15.0,24, 32, 33)'
root -l -b -q 'checkEFTshapes.C("S0",1.0, 15.0, 24, 32, 33)'
root -l -b -q 'checkEFTshapes.C("S0",1.5, 15.0, 24, 32, 33)'

root -l -b -q 'checkEFTshapes.C("S0",15.0, 15.0, 115, 32, 33)'
root -l -b -q 'checkEFTshapes.C("S0",1.0, 15.0, 115, 32, 33)'
root -l -b -q 'checkEFTshapes.C("S0",1.5, 15.0, 115, 32, 33)'






root -l -b -q 'checkEFTshapes.C("M7",15.0, 15.0, 99, 30, 31)'
root -l -b -q 'checkEFTshapes.C("M7",1.0, 15.0, 99, 30, 31)'
root -l -b -q 'checkEFTshapes.C("M7",1.5, 15.0, 99, 30, 31)'

root -l -b -q 'checkEFTshapes.C("M7",15.0, 15.0, 24, 30, 31)'
root -l -b -q 'checkEFTshapes.C("M7",1.0, 15.0, 24, 30, 31)'
root -l -b -q 'checkEFTshapes.C("M7",1.5, 15.0, 24, 30, 31)'

root -l -b -q 'checkEFTshapes.C("M7",15.0, 15.0, 115, 30, 31)'
root -l -b -q 'checkEFTshapes.C("M7",1.0, 15.0, 115, 30, 31)'
root -l -b -q 'checkEFTshapes.C("M7",1.5, 15.0, 115, 30, 31)'

root -l -b -q 'checkEFTshapes.C("M1",15.0, 15.0, 99, 28, 29)'
root -l -b -q 'checkEFTshapes.C("M1",1.0, 15.0, 99, 28, 29)'
root -l -b -q 'checkEFTshapes.C("M1",1.5, 15.0, 99, 28, 29)'

root -l -b -q 'checkEFTshapes.C("M1",15.0, 15.0, 24, 28, 29)'
root -l -b -q 'checkEFTshapes.C("M1",1.0, 15.0, 24, 28, 29)'
root -l -b -q 'checkEFTshapes.C("M1",1.5, 15.0, 24, 28, 29)'

root -l -b -q 'checkEFTshapes.C("M1",15.0, 15.0, 115, 28, 29)'
root -l -b -q 'checkEFTshapes.C("M1",1.0, 15.0, 115, 28, 29)'
root -l -b -q 'checkEFTshapes.C("M1",1.5, 15.0, 115, 28, 29)'



root -l -b -q 'checkEFTshapes.C("M0",15.0, 10.0, 99, 26, 27)'
root -l -b -q 'checkEFTshapes.C("M0",1.0, 10.0, 99, 26, 27)'
root -l -b -q 'checkEFTshapes.C("M0",1.5, 10.0, 99, 26, 27)'

root -l -b -q 'checkEFTshapes.C("M0",15.0, 10.0, 24, 26, 27)'
root -l -b -q 'checkEFTshapes.C("M0",1.0, 10.0, 24, 26, 27)'
root -l -b -q 'checkEFTshapes.C("M0",1.5, 10.0, 24, 26, 27)'

root -l -b -q 'checkEFTshapes.C("M0",15.0, 10.0, 115, 26, 27)'
root -l -b -q 'checkEFTshapes.C("M0",1.0, 10.0, 115, 26, 27)'
root -l -b -q 'checkEFTshapes.C("M0",1.5, 10.0, 115, 26, 27)'