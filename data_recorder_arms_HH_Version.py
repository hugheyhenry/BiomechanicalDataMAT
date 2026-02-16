#/usr/bin/env python3

"""
To set up a sample data recorder, you need to initialize all 
sensors, actuators, and peripherals from which you want to record.

Next, you need to specify a save location and trial name for your 
data.

Finally, you need to initialize the recorder itself along with a 
clocking loop for your setup.
"""

##################################################################
# SYSTEM IMPORTS
##################################################################

import numpy as np
from epicallypowerful.toolbox import LoopTimer, DataRecorder
from epicallypowerful.sensing import MicrostrainImus
from xscore_driver.driver import XSensorDataConsumer

##################################################################
# SET CLOCK SPECIFICATIONS
##################################################################

LOOP_RATE = 200 # operation rate [Hz]
clocking_loop = LoopTimer(LOOP_RATE)

##################################################################
# SET UP MICROSTRAIN IMUS
##################################################################

# add in "what sensor ids do you want?"
# ask what ids do you want, promt to type in 
# Ask what IDs you want before, create array, type it in english 


IMU_LOCATION_NAME = {
    '198247': 'Xiphoid',
    '198238': 'R Triceps',
    '198240': 'L Triceps',
    '198237': 'L Shoulder',
    '198236': 'L Forearm',
    '198248': 'Neck',
    '198239': 'R Forearm',
    '198246': 'R Shoulder',
    '198235': 'R hand'
}

print('Xiphoid - R Triceps - L Triceps - L Shoulder - L Forearm - Neck - R Forearm -R Shoulder - R hand')
user_input = input("Type locations separated by commas: ")
locations = [loc.strip() for loc in user_input.split(",")]

LOCATION_TO_ID = {v: k for k, v in IMU_LOCATION_NAME.items()}
MICROSTRAIN_IMU_IDS = [
    LOCATION_TO_ID[loc]
    for loc in locations
    if loc in LOCATION_TO_ID
]

MICROSTRAIN_IMU_RATE = LOOP_RATE # Set collection rate of IMUs
TARE_ON_STARTUP = False # Zero orientation on startup?
MICROSTRAIN_IMU_CHANNELS = [
    'orientx',
    'orienty',
    'orientz',
    'orientw',
    'gyrox',
    'gyroy',
    'gyroz',
    'accx',
    'accy',
    'accz',
    'roll',
    'pitch',
    'yaw',
    'm11',
    'm12',
    'm13',
    'm21',
    'm22',
    'm23',
    'm31',
    'm32',
    'm33',
]
all_imu_features = []

for imu_id in MICROSTRAIN_IMU_IDS:
    all_imu_features.extend([imu_id+'_'+channel for channel in MICROSTRAIN_IMU_CHANNELS])

# Instantiate instance of MicroStrain IMU manager
microstrain_imus = MicrostrainImus(
    imu_ids=MICROSTRAIN_IMU_IDS,
    rate=MICROSTRAIN_IMU_RATE,
    tare_on_startup=TARE_ON_STARTUP,
    verbose=False,
)

##################################################################
# SET UP XSENSOR INSOLES
##################################################################

INSOLE_LOCATIONS = ["left","right"] #
INSOLE_CHANNELS = [
    'sensor_id',
    'side',
    'force',
    'COPx',
    'COPz',
    'qx',
    'qy',
    'qz',
    'qw',
    'linx',
    'liny',
    'linz',
    'angx',
    'angy',
    'angz',
]
all_insole_features = []

for insole in INSOLE_LOCATIONS:
    all_insole_features.extend([insole+'_'+channel for channel in INSOLE_CHANNELS])

# Initialize instance of XSENSOR listener (assumes that 
# xscore-producer is running in another process)
xsensor_insoles = XSensorDataConsumer(locations=INSOLE_LOCATIONS)

##################################################################
# SET UP DATA RECORDER
##################################################################

save_dir = ''
trial_name = input("Enter trial name: ")
trial_name = trial_name if trial_name.endswith(".csv") else trial_name + ".csv"
features_to_record = []
features_to_record.extend(all_imu_features)
features_to_record.extend(all_insole_features)
data_recorder = DataRecorder(save_dir+trial_name, features_to_record, buffer_limit=100)

##################################################################
# MAIN CONTROLLER LOOP
##################################################################

# Continuously stream and record data
# Put in restart program 
while True:
    if clocking_loop.continue_loop():
        # Iterate through all connected IMUs
        data = []

        for imu_id in MICROSTRAIN_IMU_IDS:
            raw_imu_data = microstrain_imus.get_data(imu_id=imu_id)

            for channel in MICROSTRAIN_IMU_CHANNELS:
              data.extend([getattr(raw_imu_data, channel, 0)])

            # Print out raw linear acceleration for current sensor, print out here for name 
            print(f"{imu_id} - {IMU_LOCATION_NAME[imu_id]} | ({raw_imu_data.accx:.2f}, {raw_imu_data.accy:.2f}, {raw_imu_data.accz:.2f})")
        
        # Iterate through all connected XSENSOR insoles
        for insole in INSOLE_LOCATIONS:
            raw_insole_data = xsensor_insoles.get_data(insole)
            
            for channel in INSOLE_CHANNELS:
                data.extend([getattr(raw_insole_data, channel, 0)])

        # Log data to file
        data_recorder.save(data)


data_recorder.finalize()
 
