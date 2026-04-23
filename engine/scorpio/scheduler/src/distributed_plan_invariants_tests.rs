// Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.

//! Stage-boundary checks for distributed **join**, **aggregation**, and nested **aggregation** plans.
//!
//! Complements client integration tests (`scorpio` `context_checks`, `sort_shuffle`) by locking in
//! scheduler-side invariants: multiple stages and shuffle writers / unresolved shuffles when the
//! planner inserts exchange boundaries. See `docs/engine-distributed-dataframe-verification.md`.

use datafusion::physical_plan::display::DisplayableExecutionPlan;

use crate::state::execution_graph::ExecutionGraph;
use crate::test_utils::{test_aggregation_plan, test_join_plan, test_two_aggregations_plan};

fn staged_plans_concat(graph: &impl ExecutionGraph) -> String {
    graph
        .stages()
        .values()
        .map(|st| format!("{}", DisplayableExecutionPlan::new(st.plan()).indent(false)))
        .collect::<Vec<_>>()
        .join("\n")
}

fn assert_shuffle_boundary_present(graph: &impl ExecutionGraph, case: &str) {
    let text = staged_plans_concat(graph);
    let has_shuffle = text.contains("ShuffleWriterExec")
        || text.contains("SortShuffleWriterExec")
        || text.contains("UnresolvedShuffleExec");
    assert!(
        has_shuffle,
        "{case}: expected shuffle-related operators in staged plans; got:\n{text}"
    );
}

#[tokio::test]
async fn distributed_plan_invariants_partitioned_group_by() {
    let graph = test_aggregation_plan(4).await;
    assert!(
        graph.stage_count() >= 2,
        "GROUP BY over a multi-partition scan should produce at least two stages (shuffle boundary)"
    );
    assert_shuffle_boundary_present(&graph, "partitioned aggregation");
}

#[tokio::test]
async fn distributed_plan_invariants_inner_join_aggregate_sort() {
    let graph = test_join_plan(4).await;
    assert!(
        graph.stage_count() >= 2,
        "inner join + aggregate + sort should produce multiple scheduler stages"
    );
    assert_shuffle_boundary_present(&graph, "join + aggregate");
}

#[tokio::test]
async fn distributed_plan_invariants_nested_aggregations() {
    let graph = test_two_aggregations_plan(4).await;
    assert!(
        graph.stage_count() >= 2,
        "nested aggregates over partitioned input should produce multiple stages"
    );
    assert_shuffle_boundary_present(&graph, "nested aggregations");
}
