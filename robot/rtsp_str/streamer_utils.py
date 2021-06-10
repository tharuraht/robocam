# Helper classes/functions for RTSP Streamer
from enum import Enum

class Anno_modes(Enum):
    date = 0x00000004
    time = 0x00000008
    custom_text = 0x00000001
    black_bg = 0x00000400

class Video_params:
    temporal_res = [15,25,30,40]
    spatial_res = [100000, 300000, 600000, 1000000, 2000000, 5000000, 7000000, 10000000]

    def __init__(self):
        self.cur_temp_idx = 2
        self.cur_spatial_idx = 1

    def get_temporal_res(self):
        return self.temporal_res[self.cur_temp_idx]

    def get_spatial_res(self):
        return self.spatial_res[self.cur_spatial_idx]

    def change_params(self,temporal=0,spatial=0):
        """
        Changes the temporal and/or spatial parameters by increment/decrement

        +1 : increment
        0  : no change
        -1 : decrement
        """
        if temporal == 1:
            if self.cur_temp_idx < len(self.temporal_res)-1:
                self.cur_temp_idx += 1
        elif temporal == -1:
            if self.cur_temp_idx > 0:
                self.cur_temp_idx -= 1

        if spatial == 1:
            if self.cur_spatial_idx < len(self.spatial_res)-1:
                self.cur_spatial_idx += 1
        elif spatial == -1:
            if self.cur_spatial_idx > 0:
                self.cur_spatial_idx -= 1
        return

class Status(Enum):
  Stable = 1
  Fluctuated = 2
  Degraded = 3
  Non_Monotonic = 4
  Progressive = 5