// Copyright (c) 2020 Julian Bernhard, Klemens Esterle, Patrick Hart and
// Tobias Kessler
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.


#ifndef PYTHON_POLYMORPHIC_CONVERSION_HPP_
#define PYTHON_POLYMORPHIC_CONVERSION_HPP_

#include "bark/python_wrapper/common.hpp"
#include "bark/models/behavior/behavior_model.hpp"
#include "bark/world/goal_definition/goal_definition.hpp"
#include "bark/models/behavior/motion_primitives/primitives/primitive.hpp"
#ifdef LTL_RULES
#include "bark/world/evaluation/ltl/labels/base_label_function.hpp"
#endif

namespace py = pybind11;
using modules::world::goal_definition::GoalDefinitionPtr;
using modules::models::behavior::BehaviorModelPtr;
using modules::commons::ParamsPtr;
using modules::models::behavior::primitives::PrimitivePtr;

#ifdef LTL_RULES
using modules::world::evaluation::LabelFunctionPtr;
#endif

// For pickle we need conversion functions between the genereric base types and the derived types

// Behavior Models
py::tuple BehaviorModelToPython(BehaviorModelPtr behavior_model);
BehaviorModelPtr PythonToBehaviorModel(py::tuple t);

// Goal Definition
py::tuple GoalDefinitionToPython(GoalDefinitionPtr goal_definition);
GoalDefinitionPtr PythonToGoalDefinition(py::tuple t);

py::tuple ParamsToPython(const ParamsPtr& params);
ParamsPtr PythonToParams(py::tuple t);

py::tuple PrimitiveToPython(const PrimitivePtr& prim);
PrimitivePtr PythonToPrimitive(py::tuple t);

#ifdef LTL_RULES
py::tuple LabelToPython(const LabelFunctionPtr& label);
LabelFunctionPtr PythonToLabel(py::tuple t);
#endif

// Todo: Other polymorphic types, e.g. execution model...

#endif  // PYTHON_POLYMORPHIC_CONVERSION_HPP_
