import os
import sys

def FindValue(line, parameter, digits):
  	start = line.find(parameter) + len(parameter) + 2
  	line = line[start:start+digits]
  	line = line.replace('"', '')
  	return line


f = open("results/tripinfo4.xml", "r+")

durationList = []
timeLossList = []
waitingTimeList = []

for line in f:
	if "<tripinfo id" in line:
	   #Finds a value with 2 digits. 
		durationList.append(FindValue(line, "duration", 5))
		timeLossList.append(FindValue(line, "timeLoss", 5))
		waitingTimeList.append(FindValue(line, "waitingTime", 5))

def Average(lst):
	lst = list(map(float, lst))
	return sum(lst) / len(lst)


print(Average(durationList))
print(Average(timeLossList))
print(Average(waitingTimeList))


f.close()



