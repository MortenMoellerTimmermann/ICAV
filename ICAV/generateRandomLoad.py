from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import optparse
import subprocess
import random
import time
import math
import copy

argumentList = sys.argv
if(len(argumentList) != 4):
    sys.exit("Please give 3 arguements: fileName maxDepartTime AverageSpawnRate. \nFor example: 'generateRandomLoad.py routeFile 100 5'.\nThis means in 100 seconds a vehicle spawns in average every 5 seconds.")
elif((isinstance(argumentList[1],str) == False) or (argumentList[1].endswith('.xml'))):
    sys.exit("First argument has to be a string with only the name of the file, no .xml")

try:
    maxDepart = int(argumentList[2])
    averageSpawnRate = int(argumentList[3])
except ValueError as verr:
    sys.exit("Second and third arguments have to be an integers")
except Exception as ex:
    sys.exit("Stuff went wrong it seems")


fileName = argumentList[1]


rootDir = os.path.abspath(os.getcwd())
routeFile = os.path.join(rootDir, 'RouteGenerateTemplate.rou.xml')

toReplace = "<!--VEHICLE_HOLDER-->"
routeList = ["route12", "route21", "route34", "route43"]
vehicleTypeList = ["Car"]

#<vehicle depart ="0" id="car1" route="route12" type="Car"/>
vehicleString = ""
amountOfLanes = 3
CarList = []
numberOfCars = int(maxDepart / averageSpawnRate)
numberOfCars = numberOfCars * amountOfLanes

for i in range(numberOfCars):
    CarList.append([random.randint(0,maxDepart), (random.randint(0,(amountOfLanes - 1)))])

CarList.sort()

fo = open(routeFile, "r+")
str_model = fo.read()
fo.close()

if (amountOfLanes == 1):
    for i in range(numberOfCars):
        vehicleString += "<vehicle depart =\""
        vehicleString += str(CarList[i][1])
        vehicleString += "\" id=\"car" + str(i) + "\""
        vehicleString += " route=\"" + random.choice(routeList) + "\""
        vehicleString += " type=\"" + random.choice(vehicleTypeList) + "\""
        vehicleString += "/>\n"
else:
    for i in range(numberOfCars):
        vehicleString += "<vehicle depart =\""
        vehicleString += str(CarList[i][0])
        vehicleString += "\" departLane =\""
        vehicleString += str(CarList[i][1])
        vehicleString += "\" id=\"car" + str(i) + "\""
        vehicleString += " route=\"" + random.choice(routeList) + "\""
        vehicleString += " type=\"" + random.choice(vehicleTypeList) + "\""
        vehicleString += "/>\n"

str_model = str.replace(str_model, toReplace, vehicleString, 1)

modelName = os.path.join(rootDir, fileName + '.rou.xml')
text_file = open(modelName, "w")
text_file.write(str_model)
text_file.close()



