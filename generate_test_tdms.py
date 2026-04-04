# Install dependencies first: pip install nptdms numpy
from nptdms import TdmsWriter, ChannelObject
import numpy as np

with TdmsWriter("test_data.tdms") as tdms_writer:
    # Create an array of 1000 points and a sine wave
    data_time = np.linspace(0, 10, 1000)
    data_sine = np.sin(data_time)
    
    # Assign data to channels within a group
    ch1 = ChannelObject("Sensors", "Time", data_time)
    ch2 = ChannelObject("Sensors", "Sine Wave", data_sine)
    
    # Write to the file
    tdms_writer.write_segment([ch1, ch2])

print("test_data.tdms created successfully!")