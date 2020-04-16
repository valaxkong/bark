# Copyright (c) 2019 fortiss GmbH
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

try: 
  import debug_settings
except:
  print("No debugging")

import unittest
import os
from modules.runtime.scenario.scenario_generation.scenario_generation\
  import ScenarioGeneration

from modules.runtime.scenario.scenario_generation.configurable_scenario_generation \
  import ConfigurableScenarioGeneration

from modules.runtime.commons.parameters import ParameterServer

from bark.geometry import *



class ScenarioGenerationTests(unittest.TestCase):
  def test_configurable_scenario_generation_default_params(self):
    params = ParameterServer()
    scenario_generation = ConfigurableScenarioGeneration(num_scenarios=2,params=params)
    scenario_generation.dump_scenario_list("test.scenario")

    scenario_loader = ScenarioGeneration()
    scenario_loader.load_scenario_list("test.scenario")

    self.assertEqual(len(scenario_loader._scenario_list), 2)
    self.assertEqual(len(scenario_loader._scenario_list[0]._agent_list), len(scenario_generation._scenario_list[0]._agent_list))

    scenario = scenario_loader.get_scenario(idx=0)

    params.save("default_params_standard.json")

  def test_configurable_scenario_generation_interaction_merging_track_ids(self):
    sink_source_dict = {
      "SourceSink": [[1001.92, 1005.59],  [883.064, 1009.07] ],
      "Description": "merging_deu_standard",
      "ConfigAgentStatesGeometries": {"Type": "InteractionDataTrackIdsStatesGeometries"},
      "ConfigBehaviorModels": {"Type": "InteractionDataBehaviors"},
      "ConfigExecutionModels": {"Type": "FixedExecutionType"},
      "ConfigDynamicModels": {"Type": "FixedDynamicType"},
      "ConfigGoalDefinitions": {"Type": "FixedGoalTypes"},
      "ConfigControlledAgents": {"Type": "AgentIds", "ControlledIds" : [1]},
      "AgentParams" : {}
    }

    params = ParameterServer()
    params["Scenario"]["Generation"]["ConfigurableScenarioGeneration"]["SinksSources"] = [sink_source_dict]
    params["Scenario"]["Generation"]["ConfigurableScenarioGeneration"]["MapFilename"] = \
          "modules/runtime/tests/data/DR_DEU_Merging_MT_shifted.xodr"
    scenario_generation = ConfigurableScenarioGeneration(num_scenarios=2,params=params)
    scenario_generation.dump_scenario_list("test.scenario")

    scenario_loader = ScenarioGeneration()
    scenario_loader.load_scenario_list("test.scenario")

    self.assertEqual(len(scenario_loader._scenario_list), 2)
    self.assertEqual(len(scenario_loader._scenario_list[0]._agent_list), len(scenario_generation._scenario_list[0]._agent_list))

    scenario = scenario_loader.get_scenario(idx=0)

    params.save("default_params_interaction_dataset.json")

  def test_configurable_scenario_generation_interaction_merging_window(self):
    sink_source_dict = {
      "SourceSink": [[1001.92, 1005.59],  [883.064, 1009.07] ],
      "Description": "merging_deu_standard",
      "ConfigAgentStatesGeometries": {"Type": "InteractionDataWindowStatesGeometries"},
      "ConfigBehaviorModels": {"Type": "InteractionDataBehaviors"},
      "ConfigExecutionModels": {"Type": "FixedExecutionType"},
      "ConfigDynamicModels": {"Type": "FixedDynamicType"},
      "ConfigGoalDefinitions": {"Type": "FixedGoalTypes"},
      "ConfigControlledAgents": {"Type": "AgentIds", "ControlledIds" : [1]},
      "AgentParams" : {}
    }

    params = ParameterServer()
    params["Scenario"]["Generation"]["ConfigurableScenarioGeneration"]["SinksSources"] = [sink_source_dict]
    params["Scenario"]["Generation"]["ConfigurableScenarioGeneration"]["MapFilename"] = \
          "modules/runtime/tests/data/DR_DEU_Merging_MT_shifted.xodr"
    scenario_generation = ConfigurableScenarioGeneration(num_scenarios=2,params=params)
    scenario_generation.dump_scenario_list("test.scenario")

    scenario_loader = ScenarioGeneration()
    scenario_loader.load_scenario_list("test.scenario")

    self.assertEqual(len(scenario_loader._scenario_list), 2)
    self.assertEqual(len(scenario_loader._scenario_list[0]._agent_list), len(scenario_generation._scenario_list[0]._agent_list))

    scenario = scenario_loader.get_scenario(idx=0)

    # test if window is reset
    scenario_generation2 = ConfigurableScenarioGeneration(num_scenarios=2,params=params)
    self.assertEqual(len(scenario_generation2._scenario_list), 2)

    params.save("default_params_interaction_dataset.json")

  def test_configurable_scenario_generation_behavior_space_sampling(self):
    sink_source_dict = {
      "SourceSink": [[5111.626, 5006.8305],  [5110.789, 5193.1725] ],
      "Description": "left_lane",
      "ConfigAgentStatesGeometries": {"Type": "UniformVehicleDistribution", "LanePositions": [0]},
      "ConfigBehaviorModels": {"Type": "BehaviorSpaceSampling", "ModelType" : "BehaviorIDMStochastic", \
           "ModelParams" : {"BehaviorIDMStochastic::HeadwayDistribution::Range" : [10, 20],
                            "BehaviorIDMStochastic::HeadwayDistribution::Width": [0.5, 1.0]}},
      "ConfigExecutionModels": {"Type": "FixedExecutionType"},
      "ConfigDynamicModels": {"Type": "FixedDynamicType"},
      "ConfigGoalDefinitions": {"Type": "FixedGoalTypes"},
      "ConfigControlledAgents": {"Type": "NoneControlled"},
      "AgentParams" : {}
    }

    params = ParameterServer()
    params["Scenario"]["Generation"]["ConfigurableScenarioGeneration"]["SinksSources"] = [sink_source_dict]
    scenario_generation = ConfigurableScenarioGeneration(num_scenarios=2,params=params)
    scenario_generation.dump_scenario_list("test.scenario")

    scenario_loader = ScenarioGeneration()
    scenario_loader.load_scenario_list("test.scenario")

    self.assertEqual(len(scenario_loader._scenario_list), 2)
    self.assertEqual(len(scenario_loader._scenario_list[0]._agent_list), len(scenario_generation._scenario_list[0]._agent_list))

    scenario = scenario_loader.get_scenario(idx=0)

    params.save("default_params_sampling.json")

    peristed_param_servers = scenario_generation.get_persisted_param_servers()
    behavior_models_params = peristed_param_servers["ConfigBehaviorModels"][0]["ParameterServers"]
    for behavior_param in behavior_models_params:
      dct = behavior_param.convert_to_dict()
      print(dct)

  def test_find_overlaps_configurable_scenario_generation(self):
    shape = Polygon2d([0, 0, 0], [Point2d(-1,0),
                      Point2d(-1,1),
                      Point2d(1,1),
                      Point2d(1,0)])

    agent_states1 = [[0, 1, 0, 0, 0], [0, 4, 0, 0, 0], [0, 8, 0, 0, 0]] # agents along x axis
    agent_geometries1 = [shape, shape, shape]

    agent_states2 = [[0, 4, -10, 0, 0], [0, 4, 0, 0, 0], [0, 4, 20, 0, 0]] # agents along y axis at x= 4
    agent_geometries2 = [shape, shape, shape]

    agent_states3 = [[0, 20, -20, 0, 0], [0, 1, 0, 0, 0], [0, 4, 20, 0, 0]] # some agents two colliding with other configs
    agent_geometries3 = [shape, shape, shape]

    collected_sources_sinks_agent_states_geometries = [(agent_states1, agent_geometries1),
                                                  (agent_states2, agent_geometries2),
                                                  (agent_states3, agent_geometries3)]
    
    overlaps = ConfigurableScenarioGeneration.find_overlaps_in_sources_sinks_agents( 
                  collected_sources_sinks_agent_states_geometries)


    self.assertTrue("0-1" in overlaps)
    
    collisions_01 = overlaps["0-1"]
    self.assertEqual(len(collisions_01), 1)

    # check source sink configs
    self.assertEqual(collisions_01[0][0][0], 0)
    self.assertEqual(collisions_01[0][1][0], 1)

    #check agent positions in list
    self.assertEqual(collisions_01[0][0][1], 1)
    self.assertEqual(collisions_01[0][1][1], 1)
    
    self.assertTrue("0-2" in overlaps)
    
    collisions_02 = overlaps["0-2"]
    self.assertEqual(len(collisions_02), 1)

    # check source sink configs
    self.assertEqual(collisions_02[0][0][0], 0)
    self.assertEqual(collisions_02[0][1][0], 2)

    #check agent positions in list
    self.assertEqual(collisions_02[0][0][1], 0)
    self.assertEqual(collisions_02[0][1][1], 1)

    collisions_03 = overlaps["1-2"]
    self.assertEqual(len(collisions_03), 1)

    # check source sink configs
    self.assertEqual(collisions_03[0][0][0], 1)
    self.assertEqual(collisions_03[0][1][0], 2)

    #check agent positions in list
    self.assertEqual(collisions_03[0][0][1], 2)
    self.assertEqual(collisions_03[0][1][1], 2)



if __name__ == '__main__':
  unittest.main()


