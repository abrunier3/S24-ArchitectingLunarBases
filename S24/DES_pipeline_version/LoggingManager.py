import simpy
import sys
import os

# Make sure the repo root is on the path so package imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from S24.DES_pipeline_version.ISRUPlant import ISRUPlant
from S24.DES_pipeline_version.SolarPowerSystem import SolarPowerSystem
from S24.DES_pipeline_version.PowerManager import PowerManager
from S24.DES_pipeline_version.HabitationModule import HabitationModule
from S24.DES_pipeline_version.CommunicationModule import CommunicationModule
from S24.DES_pipeline_version.LunarRover import LunarRover
from S24.DES_pipeline_version.RoverChargingStation import RoverChargingStation
from S24.DES_pipeline_version.LandingLaunchZone import LandingLaunchZone
import json

class LoggingManager:
    """
    Manages periodic logging for the lunar spaceport simulation.

    Attributes:
        env (simpy.Environment): The SimPy simulation environment.
        time_step (float): How often (in simulation time units) the log
                           function should be called.
    """

    def __init__(self, env: simpy.Environment, time_step: float):
        self.env = env
        self.time_step = time_step
        self.objectList = []
        self.logDict = {}
    def setup(self):
        """
        Starts the periodic logging process. Should be called before
        env.run() to register the monitor process with SimPy.
        """
        self.env.process(self._monitor())

    def add(self, object):
        """
        Adds an object to the list of elements that need to be reported and monitored.
        """
        self.objectList.append(object)

    def _monitor(self):
        """
        Internal SimPy process that wakes up every time_step and
        calls the log function.
        """
        while True:
            self.log()
            yield self.env.timeout(self.time_step)

    def log(self):
        """
        Called every time_step. Prints the current simulation time. All classes added to the object list must have a getLoggingAttributes() function and a name attribute
        """
        #print(f"[{self.env.now:.2f} hr] Just logged")
        currentTimeLogDict = {}
        for object in self.objectList:
            attr = object.getLoggingAttributes()
            name = attr['Name']
            currentTimeLogDict[name] = attr
        self.logDict[self.env.now] = currentTimeLogDict

    def saveToJSON(self):
        with open('lunar_spaceport_log.json', 'w') as f:
            json.dump(self.logDict, f, indent=4)

# import simpy
# class LoggingManager:

#     def __init__(self, system, dt):
#         self.system = system
#         self.loggingInterval = dt

#     def setup(self):
#         #Create a function that will be called every time interval
#         self.system.process(self.log(self))

#     def addElement(self):
#         #Add an element to the array 
#         pass

#     def log(self):
#         #Log the data into a big dictionary somehow
#         while True:
#             print(f"[{self.system.now:.2f} hr] Just logged")
#             yield self.system.timeout(self.loggingInterval)
        

#     def output(self):
#         #Output the log to a JSON file
#         pass
