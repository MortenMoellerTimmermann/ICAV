
import sys
import os
import time
import string
import math
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT, call

ILowLoadResults = []
ISemiLowLoadResults = []
IMediumLoadResults = []
ISemiHighLoadResults = []
IHighLoadResults = []

LLowLoadResults = []
LSemiLowLoadResults = []
LMediumLoadResults = []
LSemiHighLoadResults = []
LHighLoadResults = []

TimeDuration = 400
CurrentLoad = 0
amountOfLanes = 3

def FindValue(line, parameter, digits):
  	start = line.find(parameter) + len(parameter) + 2
  	line = line[start:start+digits]
  	line = line.replace('"', '')
  	return line

def FindFromTo(line, fromparameter, toparameter):
    start = line.find(fromparameter)
    end = line[start + 1].find(toparameter)
    line = line[start:end]
    line = line.replace('"', '')
    return line

def Average(lst):
	lst = list(map(float, lst))
	return sum(lst) / len(lst)


for i in range(3, 5):
    print("NewLoad: " + str(i))
    if(i == 1):
        CurrentLoad = 10
    elif(i == 2):
        CurrentLoad = 5
    elif(i == 3):
        CurrentLoad = 3
    elif(i == 4):
        CurrentLoad = 2
    else:
        CurrentLoad = 1

    IavgDurations = []
    IavgTimeLoss = []
    IavgWaitTime = []
    IavgCO2Emission = []
    IavgCPUPerformance = []
    IavgMemoryPerformance = []

    LavgDurations = []
    LavgTimeLoss = []
    LavgWaitTime = []
    LavgCO2Emission = []

    CPUMax = 0
    CPUMin = 100000000
    MemoryMax = 0
    MemoryMin = 100000000

    for j in range(1, 4):
        generateLoadProcess = Popen("py generateRandomLoad.py TempLoad " + str(TimeDuration) + " " + str(CurrentLoad), stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = generateLoadProcess.communicate()
        generateLoadProcess.wait()

        print("ICAV: " + str(j))
        sumoProcess = Popen("py RunnerScript.py --nogui --sumocfg ConfigFile.sumocfg --expid 4 --port 8873 --controller icav", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        sumoProcess.wait()

        print("Light: " + str(j))
        sumoProcess = Popen("py RunnerScript.py --nogui --sumocfg ConfigFileLight.sumocfg --expid 5 --port 8873 --controller StandardTrafficLight", stdout = PIPE, stderr = PIPE, shell=True)
        out, outerror = sumoProcess.communicate()
        sumoProcess.wait()

        f = open("results/tripinfo4.xml", "r+")
        r = open("results/tripinfo5.xml", "r+")
        e1 = open("results/emission4.xml", "r+")
        e2 = open("results/emission5.xml", "r+")
        CPUfile = open("CPU-LogFile.txt", "r+")
        MemoryFile = open("LogFile.txt", "r+")


        IdurationList = []
        ItimeLossList = []
        IwaitingTimeList = []   
        Ico2Emission = 0
        ICPUPerformance = []
        IMemoryPerformance = []

        LdurationList = []
        LtimeLossList = []
        LwaitingTimeList = []
        Lco2Emission = 0

        for line in f:
            if "<tripinfo id" in line:
            #Finds a value with 2 digits. 
                IdurationList.append(FindValue(line, "duration", 5))
                ItimeLossList.append(FindValue(line, "timeLoss", 5))
                IwaitingTimeList.append(FindValue(line, "waitingTime", 5))

        for line in r:
            if "<tripinfo id" in line:
            #Finds a value with 2 digits. 
                LdurationList.append(FindValue(line, "duration", 5))
                LtimeLossList.append(FindValue(line, "timeLoss", 5))
                LwaitingTimeList.append(FindValue(line, "waitingTime", 5))


        for line in e1:
            if "<vehicle id" in line:
                newLines = line.split()
                for moreInfo in newLines:
                    if "CO2" in moreInfo:
                        Ico2Emission += float(FindFromTo(moreInfo, '"', '"'))

        for line in e2:
            if "<vehicle id" in line:
                newLines = line.split()
                for moreInfo in newLines:
                    if "CO2" in moreInfo:
                        Lco2Emission += float(FindFromTo(moreInfo, '"', '"'))

        for line in CPUfile:
            if "CPU user" in line:
                newLines = line.split()
                for moreInfo in newLines:
                    try:
                        ICPUPerformance.append(float(moreInfo))
                        if float(moreInfo) > CPUMax:
                            CPUMax = float(moreInfo)
                        if float(moreInfo) < CPUMin:
                            CPUMin = float(moreInfo)
                    except ValueError:
                        wat = 0

        for line in MemoryFile:
            if "Virtual memory" in line:
                newLines = line.split()
                for moreInfo in newLines:
                    try:
                        IMemoryPerformance.append(float(moreInfo))
                        if float(moreInfo) > MemoryMax:
                            MemoryMax = float(moreInfo)
                        if float(moreInfo) < MemoryMin:
                            MemoryMin = float(moreInfo)
                    except ValueError:
                        wat = 0

        f.close()
        r.close()
        e1.close()
        e2.close()
        CPUfile.close()
        MemoryFile.close()

        IavgDurations.append(Average(IdurationList))
        IavgTimeLoss.append(Average(ItimeLossList))
        IavgWaitTime.append(Average(IwaitingTimeList))
        IavgCO2Emission.append((Ico2Emission) / (int(TimeDuration / CurrentLoad) * amountOfLanes))
        IavgCPUPerformance.append(Average(ICPUPerformance))
        IavgMemoryPerformance.append(Average(IMemoryPerformance))

        LavgDurations.append(Average(LdurationList))
        LavgTimeLoss.append(Average(LtimeLossList))
        LavgWaitTime.append(Average(LwaitingTimeList))
        LavgCO2Emission.append((Lco2Emission) / (int(TimeDuration / CurrentLoad) * amountOfLanes))

    print("\nIcav controller:")
    print("\nLoadnr: " + str(i) + " Avgdurations for all 10 runs:")
    print(IavgDurations)
    print("\nLoadnr: " + str(i) + " Avgtimeloss for all 10 runs:")
    print(IavgTimeLoss)
    print("\nLoadnr: " + str(i) + " avgWaitTime for all 10 runs:")
    print(IavgWaitTime)
    print("\nLoadnr: " + str(i) + " avgCO2Emissions for all 10 runs:")
    print(IavgCO2Emission)
    print("\nLoadnr: " + str(i) + " avgCPUperformance for all 10 runs:")
    print(IavgCPUPerformance)
    print("\nLoadnr: " + str(i) + " Max CPU performance for all 10 runs:")
    print(CPUMax)
    print("\nLoadnr: " + str(i) + " Min CPU performance for all 10 runs:")
    print(CPUMin)
    print("\nLoadnr: " + str(i) + " avgMemoryperformance for all 10 runs:")
    print(IavgMemoryPerformance)
    print("\nLoadnr: " + str(i) + " Max Memory performance for all 10 runs:")
    print(MemoryMax)
    print("\nLoadnr: " + str(i) + " Min Memory performance for all 10 runs:")
    print(MemoryMin)


    print("\nStandard Traffic Light:")
    print("\nLoadnr: " + str(i) + " Avgdurations for all 10 runs:")
    print(LavgDurations)
    print("\nLoadnr: " + str(i) + " Avgtimeloss for all 10 runs:")
    print(LavgTimeLoss)
    print("\nLoadnr: " + str(i) + " avgWaitTime for all 10 runs:")
    print(LavgWaitTime)
    print("\nLoadnr: " + str(i) + " avgCO2Emissions for all 10 runs:")
    print(LavgCO2Emission)


    if(i == 1):
        ILowLoadResults.append(Average(IavgDurations))
        ILowLoadResults.append(Average(IavgTimeLoss))
        ILowLoadResults.append(Average(IavgWaitTime))
        ILowLoadResults.append(Average(IavgCO2Emission))
        ILowLoadResults.append(Average(IavgCPUPerformance))
        ILowLoadResults.append(CPUMax)
        ILowLoadResults.append(CPUMin)
        ILowLoadResults.append(Average(IavgMemoryPerformance))
        ILowLoadResults.append(MemoryMax)
        ILowLoadResults.append(MemoryMin)

        LLowLoadResults.append(Average(LavgDurations))
        LLowLoadResults.append(Average(LavgTimeLoss))
        LLowLoadResults.append(Average(LavgWaitTime))
        LLowLoadResults.append(Average(LavgCO2Emission))
    elif(i == 2):
        ISemiLowLoadResults.append(Average(IavgDurations))
        ISemiLowLoadResults.append(Average(IavgTimeLoss))
        ISemiLowLoadResults.append(Average(IavgWaitTime))
        ISemiLowLoadResults.append(Average(IavgCO2Emission))
        ISemiLowLoadResults.append(Average(IavgCPUPerformance))
        ISemiLowLoadResults.append(CPUMax)
        ISemiLowLoadResults.append(CPUMin)
        ISemiLowLoadResults.append(Average(IavgMemoryPerformance))
        ISemiLowLoadResults.append(MemoryMax)
        ISemiLowLoadResults.append(MemoryMin)

        LSemiLowLoadResults.append(Average(LavgDurations))
        LSemiLowLoadResults.append(Average(LavgTimeLoss))
        LSemiLowLoadResults.append(Average(LavgWaitTime))
        LSemiLowLoadResults.append(Average(LavgCO2Emission))
    elif(i == 3):
        IMediumLoadResults.append(Average(IavgDurations))
        IMediumLoadResults.append(Average(IavgTimeLoss))
        IMediumLoadResults.append(Average(IavgWaitTime))
        IMediumLoadResults.append(Average(IavgCO2Emission))
        IMediumLoadResults.append(Average(IavgCPUPerformance))
        IMediumLoadResults.append(CPUMax)
        IMediumLoadResults.append(CPUMin)
        IMediumLoadResults.append(Average(IavgMemoryPerformance))
        IMediumLoadResults.append(MemoryMax)
        IMediumLoadResults.append(MemoryMin)

        LMediumLoadResults.append(Average(LavgDurations))
        LMediumLoadResults.append(Average(LavgTimeLoss))
        LMediumLoadResults.append(Average(LavgWaitTime))
        LMediumLoadResults.append(Average(LavgCO2Emission))
    elif(i == 4):
        ISemiHighLoadResults.append(Average(IavgDurations))
        ISemiHighLoadResults.append(Average(IavgTimeLoss))
        ISemiHighLoadResults.append(Average(IavgWaitTime))
        ISemiHighLoadResults.append(Average(IavgCO2Emission))
        ISemiHighLoadResults.append(Average(IavgCPUPerformance))
        ISemiHighLoadResults.append(CPUMax)
        ISemiHighLoadResults.append(CPUMin)
        ISemiHighLoadResults.append(Average(IavgMemoryPerformance))
        ISemiHighLoadResults.append(MemoryMax)
        ISemiHighLoadResults.append(MemoryMin)

        LSemiHighLoadResults.append(Average(LavgDurations))
        LSemiHighLoadResults.append(Average(LavgTimeLoss))
        LSemiHighLoadResults.append(Average(LavgWaitTime))
        LSemiHighLoadResults.append(Average(LavgCO2Emission))
    elif(i == 5):
        IHighLoadResults.append(Average(IavgDurations))
        IHighLoadResults.append(Average(IavgTimeLoss))
        IHighLoadResults.append(Average(IavgWaitTime))
        IHighLoadResults.append(Average(IavgCO2Emission))
        IHighLoadResults.append(Average(IavgCPUPerformance))
        IHighLoadResults.append(CPUMax)
        IHighLoadResults.append(CPUMin)
        IHighLoadResults.append(Average(IavgMemoryPerformance))
        IHighLoadResults.append(MemoryMax)
        IHighLoadResults.append(MemoryMin)

        LHighLoadResults.append(Average(LavgDurations))
        LHighLoadResults.append(Average(LavgTimeLoss))
        LHighLoadResults.append(Average(LavgWaitTime))
        LHighLoadResults.append(Average(LavgCO2Emission))


print("Results for Icav - on form: Duratin, Time Loss, Wait Time, CO2Emission, CPUperformance, CPU MAX, CPU MIN, Memory Performance, Memory MAX, Memory MIN: \n")
print("Og i rækkefølge: High, semihigh, medium, semilow og low\n")
print(IHighLoadResults)
print(ISemiHighLoadResults)
print(IMediumLoadResults)
print(ISemiLowLoadResults)
print(ILowLoadResults)

print("Results for standard traffic light - on form: Duratin, Time Loss, Wait Time, CO2Emission: \n")
print("Og i rækkefølge: High, semihigh, medium, semilow og low\n")
print(LHighLoadResults)
print(LSemiHighLoadResults)
print(LMediumLoadResults)
print(LSemiLowLoadResults)
print(LLowLoadResults)

