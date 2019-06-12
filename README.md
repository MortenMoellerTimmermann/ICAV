In order to run a demo of ICAV you need the following installed:
 - SUMO (Simulation of Urban MObility) URL: https://sumo.dlr.de/index.html
 	- In case of Linux remember to set a SUMO home
 - UPPAAL (4.1.19 or newer) URL: http://uppaal.org/
 - Python 2 or 3 URL: https://www.python.org/downloads/

From a path of the /ICAV/ICAV folder run the following command:
	py RunnerScript.py --sumocfg ConfigFile.sumocfg --expid 1 --port 8873 --controller icav

Where the py is the python command. This can diffirentiate. An example could be Python3 RunnerScript.py ... instead.
The rest of the command states which SUMO config file, experiment ID, port and controller to use. In case of ICAV the controller is obviously set to icav.


In order to recreate the experiments run the following command:
	py CreateResults.py 

Again py may have to be Python3 or something else instead. To configure what the experiments test there are three different parameters that can be changed in the CreateResults.py file. 
 - TimeDuration
 - CurrentLoad
 - amountOfLanes

The TimeDuration parameter changes how many simulation steps the experiments are. This was 400 for the experiments in the paper.

The CurrentLoad parameter changes from what load the experiments are started. If this is set higher fewer iterations of the same load are run. This was 0 in the experiments in the paper.

The amountOfLanes parameter changes how many lanes the experiment is run on. This was 1 and 3 in the experiments in the paper. 

We created a file to generate loads instead of using the default SUMO file for it, as we did not want cars turning.

Feel free to change anything, explore the different files and play around with the different parameters.


