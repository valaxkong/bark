# Copyright (c) 2020 Julian Bernhard, Klemens Esterle, Patrick Hart and
# Tobias Kessler
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import numpy as np
from collections import defaultdict

from bark.runtime.scenario.scenario_generation.config_readers.config_readers_interfaces \
       import ConfigReaderAgentStatesAndGeometries

from modules.runtime.scenario.scenario_generation.interaction_dataset_reader import shape_from_track, \
    bark_state_from_motion_state, init_state_from_track, track_from_trackfile
from com_github_interaction_dataset_interaction_dataset.python.utils import dataset_reader

from bark.geometry.standard_shapes import *
from bark.geometry import *
from bark.models.dynamic import *

# this config reader defines agent states with distances sampled uniformly standard vehicle geometries models
# it can be specified with parameter "lane_position" being between 1 and num_road_corridor_lanes 
# in what lanes vehicles are placed, or if None in all lanes they are placed
class UniformVehicleDistribution(ConfigReaderAgentStatesAndGeometries):
  def create_from_config(self, config_param_object, road_corridor):
    self._lane_positions = config_param_object["LanePositions", "List of values out of 0:max_num_lanes-1. \
            Vehicles are placed only this lanes \
           or None if vehicles shall be placed at alles lanes", None]
    self._vehicle_distance_range = config_param_object["VehicleDistanceRange",
      "Distance range between vehicles in meter given as tuple from which" + \
      "distances are sampled uniformly",
      (10, 20)]
    self._other_velocity_range = config_param_object["OtherVehicleVelocityRange",
      "Lower and upper bound of velocity in km/h given as tuple from which" + \
      " velocities are sampled uniformly",
      (20,30)]
    self._s_range = config_param_object["SRange", "pair of values (tuple) between 0 and 1 to limit placement  \
                     to certain part of road corridor", (0.1, 0.7)]
    # todo make parameterizable, but not only based on 2d points
    self._vehicle_2d_shape = CarLimousine()

    agent_states = []
    agent_geometries = []
    agent_lane_positions = []

    lane_corridors, lane_positions = self.select_lane_corridors(road_corridor, self._lane_positions)
    for idx, lane_corridor in enumerate(lane_corridors):
      tmp_agent_states, tmp_agent_geometries = self.agents_along_lane_corridor(lane_corridor,
                   self._s_range[0], self._s_range[1])

      agent_states.extend(tmp_agent_states)
      agent_geometries.extend(tmp_agent_geometries)
      agent_lane_positions.extend([lane_positions[idx]]*len(tmp_agent_states))

    assert(len(agent_states) == len(agent_geometries))
    assert(len(agent_states) == len(agent_lane_positions))
    return agent_states, agent_geometries, {"agent_lane_positions": agent_lane_positions}, config_param_object


  def select_lane_corridors(self, road_corridor, lane_positions):
    lane_corridors = []
    if lane_positions:
      for lane_position in lane_positions:
        lane_corridors.append(road_corridor.lane_corridors[lane_position])
    else:
        lane_corridors = road_corridor.lane_corridors
        lane_positions = list(range(1, len(lane_corridors)+1))
    return lane_corridors, lane_positions

  def sample_velocity_uniform(self, velocity_range):
    return self.random_state.uniform(velocity_range[0], velocity_range[1])

  def sample_distance_uniform(self, distance_range):
    return self.random_state.uniform(distance_range[0], distance_range[1])


  def agents_along_lane_corridor(self,
                              lane_corridor,
                              s_start,
                              s_end):
    linestring = lane_corridor.center_line
    agent_states = []
    agent_geometries = []
    corridor_length = lane_corridor.center_line.Length()
    s = s_start*corridor_length
    while s < s_end*corridor_length:
      # set agent state on linestring with random velocity
      xy_point =  GetPointAtS(linestring, s)
      angle = GetTangentAngleAtS(linestring, s)
      
      velocity = self.sample_velocity_uniform(self._other_velocity_range)
      agent_state = [0, xy_point.x(), xy_point.y(), angle, velocity ]

      agent_states.append(agent_state)
      agent_geometries.append(self._vehicle_2d_shape)

      # move forward on linestring based on vehicle size and max/min distance
      s += self._vehicle_2d_shape.front_dist + self._vehicle_2d_shape.rear_dist + \
                  self.sample_distance_uniform(self._vehicle_distance_range)
    return agent_states, agent_geometries

class InteractionDataTrackIdsStatesGeometries(ConfigReaderAgentStatesAndGeometries):
  def create_from_config(self, config_param_object, road_corridor):
    track_file_name = config_param_object["TrackFilename", "Path to track file (csv)",
                                        "modules/runtime/tests/data/interaction_dataset_DE_merging_vehicle_tracks_000.csv"]
    track_ids = config_param_object["TrackIds", "IDs of the vehicle tracks to import.", [1]]
    start_time = config_param_object["StartTs", "Timestamp when to start the scenario (ms)", 0]
    end_time = config_param_object["EndTs","Timestamp when to end the scenario (ms)", None]
    wheel_base = config_param_object["WheelBase", "Wheelbase assumed for shape calculation", 2.7]

    agent_geometries = []
    agent_states = []
    lane_positions = []
    tracks = []
    for track_id in track_ids:
      track = track_from_trackfile(track_file_name, track_id)
      if start_time is None:
          start_time = track.time_stamp_ms_first
      if end_time is None:
          end_time = track.time_stamp_ms_last
      numpy_state = init_state_from_track(track, start_time)
      agent_state = numpy_state.reshape(5).tolist()
      agent_states.append(agent_state)
      shape = shape_from_track(track, wheel_base)
      agent_geometries.append(shape)
      tracks.append(track)
      lane_positions = self.find_lane_positions(numpy_state, road_corridor)
      lane_positions.append(lane_positions)

    assert(len(agent_states) == len(agent_geometries))
    return agent_states, agent_geometries, {"track_ids": track_ids, "tracks" : tracks, \
             "agent_ids" : track_ids, "start_time" : start_time, "end_time" : end_time, \
               "agent_lane_positions" : lane_positions}, config_param_object
  
  def find_lane_positions(self, init_state, road_corridor):
    lps = []
    for idx, lane_corridor in enumerate(road_corridor.lane_corridors):
      if Collide(lane_corridor.polygon, Point2d(init_state[int(StateDefinition.X_POSITION)], \
         init_state[int(StateDefinition.Y_POSITION)])):
        lps.append(idx)
    return lps

class InteractionDataWindowStatesGeometries(ConfigReaderAgentStatesAndGeometries):
  window_start = None
  window_end = None
  def create_from_config(self, config_param_object, road_corridor):
    track_file_name = config_param_object["TrackFilename", "Path to track file (csv)",
                                        "modules/runtime/tests/data/interaction_dataset_DE_merging_vehicle_tracks_000.csv"]
    wheel_base = config_param_object["WheelBase", "Wheelbase assumed for shape calculation", 2.7]
    window_length = config_param_object["WindowLength", "Window length for search of agents for a scenario ", 0.2]
    skip_time_delta = config_param_object["SkipTimeDelta", "Time delta between start of current and next search window", 0.1]
    min_time = config_param_object["MinTime", "Time offset from beginning of track file to start searching", 0.0]
    max_time = config_param_object["MaxTime", "Max time included in search", 100.0]
    only_on_one_lane = config_param_object["OnlyOnOneLane", "If True only scenarios are defined where agents are on a single lane", True]
    minimum_numbers_per_lane = config_param_object["MinimumNumbersPerLane", "List where each element specifies how man vehicles must be at minimum at this lane,\
                                  lane position equals list index", [1, 0]]

    # todo: would be better to load this only once for the whole scenario genarion
    track_dict = dataset_reader.read_tracks(track_file_name)
    agent_geometries = []
    agent_states = []
    lane_positions = []
    tracks = []

    # reset when a new scenario generation starts
    if self.current_scenario_idx == 0:
      InteractionDataWindowStatesGeometries.window_start = None;
      InteractionDataWindowStatesGeometries.window_end = None;

    window_start = InteractionDataWindowStatesGeometries.window_start
    window_end = InteractionDataWindowStatesGeometries.window_end

    scenario_track_ids, window_start, window_end = self.find_track_ids_moving_window(window_start, window_end, track_dict, only_on_one_lane, minimum_numbers_per_lane,
                        window_length, skip_time_delta, min_time, max_time, road_corridor)
    if len(scenario_track_ids) < 1:
      raise ValueError("No track ids found for scenario idx {}. Consider lowering the number of scenarios.".format(self.current_scenario_idx))

    for track_id in scenario_track_ids:
      numpy_state = self.get_init_state(track_dict, track_id, window_start, window_end)
      agent_state = numpy_state.reshape(5).tolist()
      agent_states.append(agent_state)
      track = track_dict[track_id]
      shape = shape_from_track(track, wheel_base)
      agent_geometries.append(shape)
      tracks.append(track)
      lane_positions = self.find_lane_positions(numpy_state, road_corridor)
      lane_positions.append(lane_positions)

    assert(len(agent_states) == len(agent_geometries))
    InteractionDataWindowStatesGeometries.window_start = window_start
    InteractionDataWindowStatesGeometries.window_end = window_end
    return agent_states, agent_geometries, {"track_ids": scenario_track_ids, "tracks" : tracks, \
             "agent_ids" : scenario_track_ids, "start_time" : window_start*1000, "end_time" : window_end*1000, \
               "agent_lane_positions" : lane_positions}, config_param_object

  def find_track_ids_moving_window(self, window_start, window_end, track_dict, only_on_one_lane, minimum_numbers_per_lane, \
                                      window_length, skip_time_delta, time_offset, max_time, road_corridor):
    def move_window(window_start, window_end):
      if window_end is None or window_start is None:
        window_start = time_offset
        window_end = window_start + window_length
      else:
        window_start += skip_time_delta
        window_end = window_start + window_length
      return window_start, window_end

    while True:
      window_start, window_end = move_window(window_start, window_end)
      if window_end > max_time:
        return [], window_start, window_end
      window_track_ids = self.find_track_ids(track_dict, window_start, window_end)
      lane_positions_valid = True
      if len(window_track_ids) < 1:
        continue

      lane_positions_valid = True
      numbers_per_lane = defaultdict(list)
      for track_id in window_track_ids:
        init_state = self.get_init_state(track_dict, track_id, window_start, window_end)
        lane_positions = self.find_lane_positions(init_state, road_corridor)
        # skip whole window if lane positions not fulfilled
        if only_on_one_lane and len(lane_positions) != 1:
          lane_positions_valid = False
          break
        numbers_per_lane[lane_positions[0]].append(track_id)
      if not lane_positions_valid:
        continue
      
      minimum_number_valid = True
      for lane_pos, minimum_number in enumerate(minimum_numbers_per_lane):
        if len(numbers_per_lane[lane_pos]) < minimum_number:
          minimum_number_valid = False
          break
      if not minimum_number_valid:
        continue
      else:
        break

    return window_track_ids, window_start, window_end

  def get_init_state(self, track_dict, track_id, start_time, end_time):
    track = track_dict[track_id]
    return init_state_from_track(track, start_time)

  def find_track_ids(self, track_dict, start_time, end_time):
    list_ids = []
    for id_current in track_dict.keys():
        if track_dict[id_current].time_stamp_ms_last / 1000.0 >= end_time and \
          track_dict[id_current].time_stamp_ms_first / 1000.0 <= start_time:
            list_ids.append(id_current)
    return list_ids

  def is_only_on_lane(self, init_state, lane_position, road_corridor):
    lane_positions = self.find_lane_positions(init_state, road_corridor)
    if len(lane_positions) == 1 and lane_position in lane_positions:
      return True
    else:
      return False

  def find_lane_positions(self, init_state, road_corridor):
    lps = []
    for idx, lane_corridor in enumerate(road_corridor.lane_corridors):
      if Collide(lane_corridor.polygon, Point2d(init_state[int(StateDefinition.X_POSITION)], \
         init_state[int(StateDefinition.Y_POSITION)])):
        lps.append(idx)
    return lps