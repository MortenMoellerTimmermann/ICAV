#!/usr/bin/python
import sys
import os
import time
import string
import math
import VerifierPath as VP
from os.path import expanduser
from subprocess import Popen, PIPE, STDOUT

rootDir = os.path.abspath(os.getcwd())
pathToResults = os.path.join(rootDir,'results')
pathToModels = os.path.join(rootDir,'Uppaal')

def runModel(com, args, query, simStep):
    query = "\"" + query + "\""
    f = Popen(com+args+query, stdout = PIPE, stderr = PIPE, shell=True)
    out, outerror = f.communicate()
    print(out)

    out_string = str(out)
    log_text = out_string.split('--')

    log_file = open("LogFile.txt", "a")
    cpu_log_file = open("CPU-LogFile.txt", "a")

    log_file.write("simStep: " + str(simStep))
    cpu_log_file.write("simStep: " + str(simStep))

    for line in log_text:
        if "Throughput" not in line:
            log_file.write("\n" + str(line))
            if "CPU" in line:
                cpu_log_file.write("\n" + str(line))


    log_file.write("\n\n\n")
    cpu_log_file.write("\n\n\n")

    cpu_log_file.close()
    log_file.close()

    #f = os.popen(com+args+query) Used for stratego
    #out = f.read()
    return outerror

def modelCaller(model,query,expId,simStep,cars):
    newModel = createModel(model,expId,simStep,cars)
    veri = VP.veri
    com = veri +  ' -o 1 -t 0 -u '
    args = "\"" + newModel + "\" "
    #newQuery = createQuery(query, expId, cars) Used for stratego
    out = runModel(com,args,query, simStep)
    carSpeeds = getStrategy(out, cars)
    
    #' -o 1 -t 0 '
    """
    ' --learning-method ' + str(3) \
      + ' --good-runs ' + str(20) \
      + ' --total-runs ' + str(20) \
      + ' --runs-pr-state ' + str(30) \
      + ' --eval-runs ' + str(10) \
      + ' --max-iterations ' + str(10) \
      + ' --filter 0 '
    """
    
    return carSpeeds

def getStrategy(outStr, cars):
    carSpeeds = []

    for i in range (0,len(cars)):
        strStart = "Cars(" + str(i) + ").newSpeed"
        #carSpeeds.append(float(strategoGetSubString(outStr,strStart)))
        carSpeeds.append(float(standardGetSubString(outStr,strStart)))

    print("new speeds:" + str(carSpeeds))
 
    return carSpeeds

def strategoGetSubString(outStr, key):
    speedLoc = "(1,"
    key_len = len(key)
    found = outStr.find(key)
    start = found + key_len + 11
    end = outStr.find(speedLoc, start) + len(speedLoc) + 3
    value = (outStr[start:end]).strip()
    return value[:-1]

def standardGetSubString(outStr, key):
    delim = "="
    key_len = len(key)
    outStr = str(outStr)
    found = outStr.rfind(key)
    start = found + key_len
    end = outStr.find(delim, start) + len(delim) + 2
    value = (outStr[start:end]).strip()
    return value[1:]

def createModel(master_model,expId,simStep,cars):
    fo = open(master_model, "r+")
    str_model = fo.read()
    fo.close()

    toReplace = "//HOLDER_NUMBER_OF_CARS"
    value = "const int N = " + str(len(cars)) + ";\n"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_PID"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][0][-1:]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_SPEED"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][1]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_LENGTH"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][2]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_WIDTH"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][3]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)
    
    toReplace = "//HOLDER_CAR_POSX"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][4]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_POSY"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][5]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_ROUTE"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][6]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_DECEL"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][7]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_ACCEL"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][8]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_MAXSPEED"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][9]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_DESIREDSPEED"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][10]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_CAR_SETSPEED"
    value = "{"
    for i in range (0,len(cars)):
        value += str(cars[i][11]) + ","
    value = value[:-1]
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_SIM_STEP"
    value = "int sim_step = " + str(simStep) + ";"
    str_model = str.replace(str_model, toReplace, value, 1)

    modelName = os.path.join(pathToModels, 'tempModel' + str(expId) + '.xml')
    text_file = open(modelName, "w")
    text_file.write(str_model)
    text_file.close()
    return modelName

def createQuery(master_query,expId,cars):
    fo = open(master_query, "r+")
    str_query = fo.read()
    fo.close()

    toReplace = "/*HOLDER_CAR_QUERY*/"
    value = ""
    for i in range (0,len(cars)):
        value += " Cars(" + str(i) + ").newSpeed,"
    value = value[:-1]
    str_query = str.replace(str_query, toReplace, value, 1)

    queryName = os.path.join(pathToModels, 'tempQuery' + str(expId) + '.q')
    text_file = open(queryName, "w")
    text_file.write(str_query)
    text_file.close()
    return queryName

