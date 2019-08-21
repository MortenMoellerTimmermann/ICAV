#!/usr/bin/env python
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
import re
from shapely.geometry import LineString
# we need to import python modules from the $SUMO_HOME/tools directory
try:
     tools = os.path.join(os.environ['SUMO_HOME'], "tools")
     sys.path.append(tools)
except:   
     sys.exit("please declare environment variable 'SUMO_HOME'")

from sumolib import checkBinary
import traci
from CallModel import modelCaller
from RouteDict import route_dictionary
from xml.dom import minidom

# the port used for communicating with your sumo instance
PORT = 8873

rootDir = os.path.abspath(os.getcwd())
pathToResults = os.path.join(rootDir,'results')
pathToModels = os.path.join(rootDir,'Uppaal')
icavQuery = os.path.join(pathToModels, 'ICAV.q')
icavModel = os.path.join(pathToModels, 'IcavSpeedIterationUpdate.xml')
ListOfReservations = []
xData = []
yData = []
Scaler = 10

ListOfRoutes = []
ListOfRouteNames = []
centerOfInterscetion = (0,0)
IcavTempModel = ''


def run(options):
    """execute the TraCI control loop"""
    traci.init(options.port)
    print("Configuring intersection")

    IcavTempModel, centerOfInterscetion = GenerateFlowForIntersection(pathToModels, options.sumocfg)

    print("starting run")
    step = 0
    numDetectors = 8
    carsPassed = [0] * numDetectors
    carsJammed = [0] * numDetectors
    carsJammedMeters = [0] * numDetectors
    carsPassinge1 = [0] * numDetectors
    meanSpeed = [0] * numDetectors

    CarIDList = []
    ListOfCarsPlaceholder = []
    DictOfDesiredSpeeds = dict()
    LastCalled = 0

    #Used to log icav performance
    if options.controller == "icav":
        log_file = open("LogFile.txt", "w")
        log_file.write("-- LOGFILE --\n")
        log_file.close()

        log_file = open("CPU-LogFile.txt", "w")
        log_file.write("-- CPU-LOGFILE --\n")
        log_file.close()

    #detec for controller    
    #areDet = ["left_1", "right_1", "up_1", "down_1","out_left_1", "out_right_1", "out_up_1",  "out_down_1", ]
    #incomingDet = ["incoming_left_1",  "incoming_right_1",  "incoming_up_1",  "incoming_down_1"]
    #outDet = ["out_left_1", "out_right_1",  "out_up_1",  "out_down_1"]
    #ChangeBackDet = ["outgoing_out_left_1",  "outgoing_out_right_1", "outgoing_out_up_1", "outgoing_out_down_1"]

    # meassuring performance per leg in intersection
    # left A1 down B1
    legs = ["A1","A2","B1","B2"]
    detLegH = {}
    detLegH["A1"] = [ "left_1"]
    detLegH["A2"] = [ "right_1"]
    detLegH["B1"] = [ "down_1"]
    detLegH["B2"] = [ "up_1"] 
    jamMetLegH = {}
    jamMetLegH["A1"] = 0.0
    jamMetLegH["A2"] = 0.0
    jamMetLegH["B1"] = 0.0
    jamMetLegH["B2"] = 0.0
    jamCarLegH = {}
    jamCarLegH["A1"] = 0
    jamCarLegH["A2"] = 0
    jamCarLegH["B1"] = 0
    jamCarLegH["B2"] = 0
    
    totalJam = 0
    totalJamMeters = 0
    totalC02Emission = 0

    print("Starting simulation expid=" + str(options.expid))
    #additionalInfoFile = pathToResults+"additionalInfo"+str(options.expid)+".addcsv"
    #fout = open(additionalInfoFile, "w")
    #add_additional_info_header(fout,legs)
    
    while traci.simulation.getMinExpectedNumber() > 0:
        print(">>>simulation step: " + str(step))
        #carsPassinge2 and carsJammed are used by stratego, they provide partial information        
        #carsJammed = get_det_func(traci.areal.getJamLengthVehicle,areDet)
        #carsJammedMeters = get_det_func(traci.areal.getJamLengthMeters,areDet)
        #meanSpeed = get_det_func(traci.areal.getLastStepMeanSpeed,areDet)
        #jamCarLegH, jamMetLegH = get_messurements(legs, detLegH, jamCarLegH, jamMetLegH,
                                                    #traci.areal.getJamLengthVehicle,
                                                    #traci.areal.getJamLengthMeters)



        if options.controller == "GetCoordinates":
            ListOfCars = traci.vehicle.getIDList()
            
            for carID in ListOfCars:
                traci.vehicle.setSpeed(carID, 1)
                if(route_dictionary[traci.vehicle.getRoute(carID)] == 41):
                    xData.append(traci.vehicle.getPosition(carID)[0])
                    yData.append(traci.vehicle.getPosition(carID)[1])
                
        if options.controller == "StandardTrafficLight":
            ListOfCars = traci.vehicle.getIDList()

            for carID in ListOfCars:
                traci.vehicle.getSpeed(carID)


        if options.controller == "icav":
            #CarsDet = get_det_func(traci.areal.getLastStepVehicleIDs,areDet)
            #CarsOutDet = get_det_func(traci.areal.getLastStepVehicleIDs,outDet)
            #CarsIncomingDet =  get_det_func(traci.areal.getLastStepVehicleIDs,incomingDet)
            #ChangeCarsBackDet = get_det_func(traci.areal.getLastStepVehicleIDs,ChangeBackDet)

            ListOfCars = []
            ListOfCarIDs = []
            Speeds = []
            carTuple = ()
            ShouldCall = 0
            ShouldCallModel = False
            GapDistance = 5

            MiddleCoordinates = list(centerOfInterscetion)
            CarCoordinates = []
            CarsInNetworkList = traci.vehicle.getIDList()

            #print(traci.edge.getCO2Emission("Road1"))

            for Car in CarsInNetworkList:
                CarCoordinates = []
                CarCoordinates.append(traci.vehicle.getPosition(Car)[0])
                CarCoordinates.append(traci.vehicle.getPosition(Car)[1])
                DistanceToMiddle = euclidian(CarCoordinates, MiddleCoordinates) - GapDistance

                if (DistanceToMiddle < 190) & (DistanceToMiddle > 140):
                    traci.vehicle.setSpeed(Car, round(traci.vehicle.getSpeed(Car)))

                elif (DistanceToMiddle <= 140):
                    #Changing the vehicles to be fully autonomous and in our control
                    traci.vehicle.setEmergencyDecel(Car, 0)
                    traci.vehicle.setSpeedFactor(Car, 1)
                    traci.vehicle.setImperfection(Car, 0.0)
                    traci.vehicle.setParameter(Car, "jmIgnoreFoeProb", "100.0")
                    traci.vehicle.setParameter(Car, "jmIgnoreFoeSpeed", "100.0")
                    traci.vehicle.setParameter(Car, "speedDev", "0")
                    traci.vehicle.setParameter(Car, "Tau", "-100.0")
                    traci.vehicle.setParameter(Car, "minGap", "0.0")
                    traci.vehicle.setLaneChangeMode(Car,768)
                    #traci.vehicle.setMinGap(det[i], 0)
                    #traci.vehicle.deactivateGapControl(det[i])


                    if(Car not in ListOfCarsPlaceholder):
                        ShouldCall = 1
                    else:
                        ShouldCall = 0
                    
                    ListOfCarIDs.append(Car)

                    carTuple = (Car, 
                                int(round(traci.vehicle.getSpeed(Car))*Scaler),
                                int(round(traci.vehicle.getLength(Car))*Scaler),
                                int(round(traci.vehicle.getWidth(Car))*Scaler), 
                                int(round((traci.vehicle.getPosition(Car)[0]))*Scaler),
                                int(round((traci.vehicle.getPosition(Car)[1]))*Scaler),
                                traci.vehicle.getRoute(Car),
                                int(round(traci.vehicle.getDecel(Car))*Scaler),
                                int(round(traci.vehicle.getAccel(Car))*Scaler),
                                int(round(traci.vehicle.getMaxSpeed(Car))*Scaler),
                                int(round((DictOfDesiredSpeeds[Car] if Car in DictOfDesiredSpeeds.keys() else 0),2)*Scaler),
                                ShouldCall,
                                traci.vehicle.getLaneID(Car)[-1:])
                    ListOfCars.append(carTuple)
                    #print("x: " + str(traci.vehicle.getPosition(det[i])[0]) + " y: " + str(traci.vehicle.getPosition(det[i])[1]))
            

            ListOfCars = list(set(ListOfCars))
            ListOfCarIDs = list(set(ListOfCarIDs))
            ListOfCars.sort(key=lambda tup: tup[11], reverse=False)

            amountGettingSpeed = 0
            for i in range(0, len(ListOfCars)):
                if(ListOfCars[i][11] == 1):
                    amountGettingSpeed = amountGettingSpeed + 1

            #print(ListOfCars)
            print("Amount of cars: " + str(len(ListOfCars)) + " - Cars getting a speed assigned: " + str(amountGettingSpeed))
            print("Of the format: [carID, speed, length, width, x-pos, y-pos, route, decel, accel, maxspeed, desiredspeed, speedSet]")
            print(ListOfCars)
            
            
            #Calling Uppaal with the modelcaller function
            for i in range(0,len(ListOfCarIDs)):
                if(ListOfCarIDs[i] not in ListOfCarsPlaceholder):
                    ShouldCallModel = True

            # or (step % 15 == 0 and LastCalled >= 8) Used if the model needs to be called in intervals as well

            if(ShouldCallModel):
                speedFromModel = modelCaller(IcavTempModel, icavQuery, options.expid, step, ListOfCars, ListOfRoutes, ListOfRouteNames,centerOfInterscetion, FindMaxListLength(ListOfRoutes))
                changeCarSpeeds(ListOfCars, speedFromModel)
                LastCalled = 0
                for i in range(0,len(ListOfCarIDs)):
                    speedTuple = (ListOfCars[i][0], speedFromModel[i])
                    Speeds.append(speedTuple)
            else:
                LastCalled += 1

            ListOfCarsPlaceholder = list(ListOfCarIDs)
            if(Speeds):
                DictOfDesiredSpeeds = dict(Speeds)


            #Teleport cars out in order to avoid crashes outside our radius
            #for det in ChangeCarsBackDet:
            #    for i in range(0, len(det)):
            #        if det[i] != '':

            #manage_cars(ListOfCars, step)


            #Used to get total amount of cars in the system
            #manage_total_car_list(CarIDList, CarsDet)
            #time_and_speed_in_network(CarIDList, CarsDet)


        traci.simulationStep()
        step += 1

    #print("total carsJammed: " + str(totalJam))   
    

    traci.close()
    sys.stdout.flush()
    save_results(options.expid,options.controller,options.sumocfg,
                     step, legs, jamCarLegH, jamMetLegH)
    #fout.close()


def changeCarSpeeds(cars, speeds):
    for i in range(0,len(cars)):
        traci.vehicle.setSpeed(cars[i][0],speeds[i])
        

def manage_total_car_list(CarList, detectors):
    for det in detectors:
        for i in range(0, len(det)):
            duplicate = False
            for car in CarList:
                if car.CarID == det[i]:
                    duplicate = True
            if duplicate == False:
                CarList.append(Car(det[i], 0, 0))

def time_and_speed_in_network(CarList, indetectors):
    temporyList = []
    for det in indetectors:
        for i in range(0, len(det)):
            temporyList.append(det[i])

    for car in CarList:
        for det in indetectors:
            for i in range(0, len(det)):
                if car.CarID == det[i]:
                    car.TimeInNetwork += 1
                    car.TotalSpeed += traci.vehicle.getSpeed(det[i])
                    #print("Car: " + car.CarID + " - " + str(car.TimeInNetwork) + " ticks")
         

def add_additional_info_header(filename,legs):
    csvdata = "step,tlState"
    for i in range(0,len(legs)):
        csvdata = csvdata + "," + legs[i]
    csvdata = csvdata + "\n"    
    filename.write(csvdata)

def euclidian(CarCoordinates, MiddleCoordinates):
    return math.sqrt(((CarCoordinates[0] - float(MiddleCoordinates[0])) ** 2) + ((CarCoordinates[1] - float(MiddleCoordinates[1])) ** 2))
    
def get_messurements(legs, detLegH, jamCarLegH, jamMetLegH, funJamCar, funJamMet):
    numLegs = len(legs)
    for i in range(0,numLegs):
        dets_leg_i = detLegH[legs[i]]
        num_dets = len(dets_leg_i)
        for j in range(0,num_dets):
            jamCarLegH[legs[i]] = jamCarLegH[legs[i]] + funJamCar(dets_leg_i[j])
            jamMetLegH[legs[i]] = jamMetLegH[legs[i]] + funJamMet(dets_leg_i[j])
    return jamCarLegH, jamMetLegH
    

def GenerateFlowForIntersection(pathToModel, cfg):
    listofIds = traci.route.getIDList()

    cfgfile = minidom.parse(cfg)
    netfile = cfgfile.getElementsByTagName('net-file')

    nfile = minidom.parse(netfile[0].attributes['value'].value)
    connections = nfile.getElementsByTagName('connection')
    junctions = nfile.getElementsByTagName('junction')
    LongestJunctions = 0
    currentCenterPoint = (0,0)
    ListOfRouteIDs = []
    ListOfNonIntersectingRoutes = []

    #Find center of junction
    for junction in junctions:
        if(junction.hasAttribute('incLanes')):
            if(len(junction.attributes['incLanes'].value) > LongestJunctions):
                LongestJunctions = len(junction.attributes['incLanes'].value)
                lst = list(currentCenterPoint)
                lst[0] = junction.attributes['x'].value
                lst[1] = junction.attributes['y'].value
                currentCenterPoint = tuple(lst)

    CenterOfInterscetion = currentCenterPoint

    #Create the names of each route
    for connection in connections:
        if(connection.hasAttribute('via')):
            RouteFrom = connection.attributes['from'].value
            RouteVia = connection.attributes['via'].value
            RouteTo = connection.attributes['to'].value
            
            for i in range(0, traci.edge.getLaneNumber(RouteFrom)):
                Route = []
                FromShape = traci.lane.getShape(RouteFrom + '_' + str(i))
                ToShape = traci.lane.getShape(RouteTo + '_' + str(i))
                ViaShape = traci.lane.getShape(RouteVia)

                for j in range(0,len(FromShape)):
                    Route.append(FromShape[j])
                for j in range(0,len(ViaShape)):
                    Route.append(ViaShape[j])
                for j in range(0,len(ToShape)):
                    Route.append(ToShape[j])

                ListOfRoutes.append(Route)
                ListOfRouteNames.append('From' + RouteFrom + 'To' + RouteTo + 'On' + str(i))
     
    #Remove Duplicates 
    for i in range(0, len(ListOfRoutes)):
        ListOfRoutes[i] = list(set(ListOfRoutes[i]))

    maxListLenght = FindMaxListLength(ListOfRoutes)

    for i in range(0, len(ListOfRoutes)):
        OuterLine = LineString(ListOfRoutes[i])
        for k in range(0, len(ListOfRoutes)):
            InnerLine = LineString(ListOfRoutes[k])

            if(OuterLine.intersection(InnerLine).is_empty):
                intersectingTuple = (i,k)
                ListOfNonIntersectingRoutes.append(intersectingTuple)

    #Scale each element and fill each list to have the same amount of elements
    for i in range(0, len(ListOfRoutes)):
        for j in range(0,len(ListOfRoutes[i])):
            ListOfRoutes[i][j] = list(ListOfRoutes[i][j])
            for k in range(0,len(ListOfRoutes[i][j])):
                ListOfRoutes[i][j][k] = int(ListOfRoutes[i][j][k] * Scaler)
            ListOfRoutes[i][j] = tuple(ListOfRoutes[i][j])
            
        while(len(ListOfRoutes[i]) < maxListLenght):
            ListOfRoutes[i].append((32767,32767))

    return GiveUppaalInfo(ListOfRoutes, ListOfRouteNames, maxListLenght, ListOfNonIntersectingRoutes), CenterOfInterscetion

def GiveUppaalInfo(Routes, RouteNames, maxListLenght, ListOfNonIntersectingRoutes):
    fo = open(icavModel, "r+")
    str_model = fo.read()
    fo.close()

    toReplace = "//HOLDER_AMOUNT_OF_ROUTES"
    value = str(len(RouteNames)) + ';'
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//AMOUNT_HOLDER_NON_INTERSECTING_ROUTES"
    value = str(len(ListOfNonIntersectingRoutes)) + ';'
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_ROUTES"
    value = ""
    for i in range (0,len(RouteNames)):
        valueString = str(Routes[i]) + '; \n'
        valueString = valueString.replace('[','{')
        valueString = valueString.replace(']','}')
        valueString = valueString.replace('(','{')
        valueString = valueString.replace(')','}')
        value += 'const point ' + RouteNames[i] + '[' + str(maxListLenght) + ']' + ' = ' + valueString
    str_model = str.replace(str_model, toReplace, value, 1)

    toReplace = "//HOLDER_NON_INTERSECTING_ROUTES"
    value = "{"
    i = 0
    for element in ListOfNonIntersectingRoutes:
        value += str(element) + ","
        i = i + 1
        if(i%20 == 0):
            value += "\n"
    value = value[:-1]
    value = value.replace('[','{')
    value = value.replace(']','}')
    value = value.replace('(','{')
    value = value.replace(')','}')
    value += "};"
    str_model = str.replace(str_model, toReplace, value, 1)


    modelName = os.path.join(pathToModels, 'tempModel' + str(options.expid) + '.xml')
    text_file = open(modelName, "w")
    text_file.write(str_model)
    text_file.close()
    return modelName

def FindMaxListLength(lst): 
    maxList = max(lst, key = len) 
    maxLength = max(map(len, lst)) 
      
    return maxLength 
        
def save_results(expid,controller,scenario,totalSimTime, legs, jamCarLegH, jamMetLegH):
    numLegs = len(legs)
    totalJamMeters = 0.0
    totalJam = 0
    strJamMetLeg = ""
    strJamCarLeg = ""
    for i in range(0,numLegs):
        totalJamMeters = totalJamMeters + jamMetLegH[legs[i]]
        strJamMetLeg = strJamMetLeg + "," + str(jamMetLegH[legs[i]])        
        totalJam = totalJam + jamCarLegH[legs[i]]
        strJamCarLeg = strJamCarLeg + "," + str(jamCarLegH[legs[i]])
    
    filename = pathToResults+"exp"+str(expid)+".csv"
    csvdata = str(expid) \
      + "," + controller \
      + "," + scenario  \
      + "," + str(totalJamMeters) \
      + "," + str(totalJam) \
      + "," + str(totalSimTime) \
      + strJamMetLeg + strJamCarLeg \
      + "\n"
    with open(filename, 'w') as f:        
        f.write(csvdata)
        f.close()

def countJam(carsJammed):
    numDet = len(carsJammed) 
    res = 0
    for i in range(0,numDet):
        res = res + carsJammed[i]
    return res

def get_det_func(func,dets):
    numDet = len(dets)
    res = [0] * numDet
    for deti in range(0,numDet):
        res[deti] = func(dets[deti])
    return res   

def debug_print(options, msg):
    if options.debug:
        print(msg)
        
def get_options():
    optParser = optparse.OptionParser()
    optParser.add_option("--nogui", action="store_true",
                         default=False, help="run the commandline version of sumo")
    optParser.add_option("--debug", action="store_true",
                         default=False, help="display debug information")
    optParser.add_option("--port", type="int", dest="port",default=8873)
    optParser.add_option("--expid", type="int", dest="expid")
    optParser.add_option("--sumocfg", type="string", dest="sumocfg",
                             default="data/nylandsvejPlain.sumocfg")
    optParser.add_option("--load", type="string", dest="load",default="reserve")
    optParser.add_option("--controller", type="string", dest="controller",default="static")    
    options, args = optParser.parse_args()
    return options

                  
# this is the main entry point of this script
if __name__ == "__main__":
    options = get_options()
    print("im am here: " + os.getcwd())
    if options.nogui:
        sumoBinary = checkBinary('sumo')
    else:
        sumoBinary = checkBinary('sumo-gui')
    # this is the normal way of using traci. sumo is started as a
    # subprocess and then the python script connects and runs
    emissioninfofile = "results/emission" + str(options.expid) + ".xml"
    tripinfofile = "results/tripinfo" + str(options.expid) + ".xml"
    sumoProcess = subprocess.Popen([sumoBinary, "-c", options.sumocfg, "--tripinfo-output", 
                                    tripinfofile, "--emission-output", emissioninfofile, "--remote-port", str(options.port)], stdout=sys.stdout,
                                   stderr=sys.stderr)
    run(options)
    sumoProcess.wait()