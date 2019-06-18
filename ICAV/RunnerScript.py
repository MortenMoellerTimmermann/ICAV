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
#import pandas as pd

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

# the port used for communicating with your sumo instance
PORT = 8873

rootDir = os.path.abspath(os.getcwd())
pathToResults = os.path.join(rootDir,'results')
pathToModels = os.path.join(rootDir,'Uppaal')
icavQuery = os.path.join(pathToModels, 'ICAV.q')
icavModel = os.path.join(pathToModels, 'IcavSpeedNewClock.xml')
ListOfReservations = []
xData = []
yData = []
Scaler = 10


def run(options):
    """execute the TraCI control loop"""
    print("starting run")
    traci.init(options.port)
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

            MiddleCoordinates = [500, 500]
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
                                int(route_dictionary[traci.vehicle.getRoute(Car)]),
                                int(round(traci.vehicle.getDecel(Car))*Scaler),
                                int(round(traci.vehicle.getAccel(Car))*Scaler),
                                int(round(traci.vehicle.getMaxSpeed(Car))*Scaler),
                                int(round((DictOfDesiredSpeeds[Car] if Car in DictOfDesiredSpeeds.keys() else 0),2)*Scaler),
                                ShouldCall)
                    ListOfCars.append(carTuple)
                    #print("x: " + str(traci.vehicle.getPosition(det[i])[0]) + " y: " + str(traci.vehicle.getPosition(det[i])[1]))

    
            ListOfCars = list(set(ListOfCars))
            ListOfCarIDs = list(set(ListOfCarIDs))
            ListOfCars.sort(key=lambda tup: tup[11], reverse=True)
            #print(ListOfCars)


            
            #Calling Uppaal with the modelcaller function
            for i in range(0,len(ListOfCarIDs)):
                if(ListOfCarIDs[i] not in ListOfCarsPlaceholder):
                    ShouldCallModel = True

            # or (step % 15 == 0 and LastCalled >= 8) Used if the model needs to be called in intervals as well

            if(ShouldCallModel):
                speedFromModel = modelCaller(icavModel, icavQuery, options.expid, step, ListOfCars)
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
    return math.sqrt(((CarCoordinates[0] - MiddleCoordinates[0]) ** 2) + ((CarCoordinates[1] - MiddleCoordinates[1]) ** 2))
    
def get_messurements(legs, detLegH, jamCarLegH, jamMetLegH, funJamCar, funJamMet):
    numLegs = len(legs)
    for i in range(0,numLegs):
        dets_leg_i = detLegH[legs[i]]
        num_dets = len(dets_leg_i)
        for j in range(0,num_dets):
            jamCarLegH[legs[i]] = jamCarLegH[legs[i]] + funJamCar(dets_leg_i[j])
            jamMetLegH[legs[i]] = jamMetLegH[legs[i]] + funJamMet(dets_leg_i[j])
    return jamCarLegH, jamMetLegH
    

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