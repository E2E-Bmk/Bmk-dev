package integration;

import com.fasterxml.jackson.databind.JsonNode;
import oraclesupport.MavenFixture;
import oraclesupport.MavenFixture.RunResult;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Cross-goal, cross-format, and cross-configuration black-box checks. */
public class GoalCompositionIntegrationTest {
  private static RunResult dot;
  private static RunResult json;
  private static RunResult text;
  private static RunResult gml;
  private static RunResult puml;
  private static RunResult excludedText;
  private static RunResult excludedJson;
  private static RunResult includedDot;
  private static RunResult includedJson;
  private static RunResult firstPath;
  private static RunResult secondPath;
  private static RunResult nonDotStyleBase;
  private static RunResult nonDotMissingStyle;
  private static RunResult targetText;
  private static RunResult targetJson;
  private static RunResult reactorDot;
  private static RunResult reactorJson;
  private static RunResult reactorCoordinates;
  private static RunResult aggregateReduced;
  private static RunResult aggregateExpanded;
  private static RunResult aggregateParents;
  private static RunResult aggregateNoParents;
  private static RunResult aggregateByGroup;
  private static RunResult aggregateScopesSeparate;
  private static RunResult aggregateScopesMerged;
  private static RunResult renderedImage;
  private static RunResult externalText;
  private static RunResult externalJson;
  private static RunResult externalExcluded;
  private static RunResult invalidExternal;
  private static RunResult exampleFirst;
  private static RunResult exampleSecond;
  private static RunResult byGroupText;
  private static RunResult byGroupJson;
  private static RunResult styledDot;
  private static RunResult styledJson;

  @BeforeAll
  static void executeReferenceScenarios() throws Exception {
    dot = MavenFixture.project("graph", "-DgraphFormat=dot", "-DoutputFileName=base");
    json = MavenFixture.project("graph", "-DgraphFormat=json", "-DoutputFileName=base");
    text = MavenFixture.project("graph", "-DgraphFormat=text", "-DoutputFileName=base");
    gml = MavenFixture.project("graph", "-DgraphFormat=gml", "-DoutputFileName=base");
    puml = MavenFixture.project("graph", "-DgraphFormat=puml", "-DoutputFileName=base");
    excludedText = MavenFixture.project("graph", "-DgraphFormat=text",
        "-Dexcludes=com.fasterxml.jackson.core:jackson-databind", "-DoutputFileName=excluded");
    excludedJson = MavenFixture.project("graph", "-DgraphFormat=json",
        "-Dexcludes=com.fasterxml.jackson.core:jackson-databind", "-DoutputFileName=excluded");
    includedDot = MavenFixture.project("graph", "-DgraphFormat=dot",
        "-Dincludes=dev.spec2repo.aurora:amber-lattice,org.junit.jupiter:*", "-DoutputFileName=included");
    includedJson = MavenFixture.project("graph", "-DgraphFormat=json",
        "-Dincludes=dev.spec2repo.aurora:amber-lattice,org.junit.jupiter:*", "-DoutputFileName=included");
    firstPath = MavenFixture.project("graph", "-DgraphFormat=text",
        "-DoutputDirectory=@ROOT@/first/location", "-DoutputFileName=one");
    secondPath = MavenFixture.project("graph", "-DgraphFormat=text",
        "-DoutputDirectory=@ROOT@/second/location", "-DoutputFileName=two");
    nonDotStyleBase = MavenFixture.project("graph", "-DgraphFormat=json", "-DoutputFileName=no-style");
    nonDotMissingStyle = MavenFixture.project("graph", "-DgraphFormat=json",
        "-DcustomStyleConfiguration=@ROOT@/missing.json", "-DprintStyleConfiguration=true",
        "-DcreateImage=true", "-DoutputFileName=ignored-style");
    String customStyle = "{\"graph\":{\"rankdir\":\"LR\"},"
        + "\"default-node\":{\"type\":\"ellipse\",\"color\":\"#123456\"}}";
    styledDot = MavenFixture.dependencyProjectWithFiles("graph",
        MavenFixture.files("custom-style.json", customStyle),
        "-DgraphFormat=dot", "-DcustomStyleConfiguration=@ROOT@/custom-style.json",
        "-DoutputFileName=styled-integration");
    styledJson = MavenFixture.dependencyProjectWithFiles("graph",
        MavenFixture.files("custom-style.json", customStyle),
        "-DgraphFormat=json", "-DcustomStyleConfiguration=@ROOT@/custom-style.json",
        "-DoutputFileName=no-style");
    targetText = MavenFixture.project("graph", "-DgraphFormat=text",
        "-DtargetIncludes=org.apiguardian:apiguardian-api", "-DoutputFileName=targeted");
    targetJson = MavenFixture.project("graph", "-DgraphFormat=json",
        "-DtargetIncludes=org.apiguardian:apiguardian-api", "-DoutputFileName=targeted");
    reactorDot = MavenFixture.reactor("reactor", "-DgraphFormat=dot", "-DoutputFileName=reactor");
    reactorJson = MavenFixture.reactor("reactor", "-DgraphFormat=json", "-DoutputFileName=reactor");
    reactorCoordinates = MavenFixture.reactor("reactor", "-DgraphFormat=text",
        "-DshowGroupIds=true", "-DshowVersions=true", "-DoutputFileName=reactor-coordinates");
    aggregateReduced = MavenFixture.reactor("aggregate", "-DgraphFormat=json",
        "-DreduceEdges=true", "-DoutputFileName=aggregate-reduced");
    aggregateExpanded = MavenFixture.reactor("aggregate", "-DgraphFormat=json",
        "-DreduceEdges=false", "-DoutputFileName=aggregate-expanded");
    aggregateParents = MavenFixture.reactor("aggregate", "-DgraphFormat=text",
        "-DincludeParentProjects=true", "-DoutputFileName=aggregate-parents");
    aggregateNoParents = MavenFixture.reactor("aggregate", "-DgraphFormat=text",
        "-DincludeParentProjects=false", "-DoutputFileName=aggregate-no-parents");
    aggregateByGroup = MavenFixture.reactor("aggregate-by-groupid", "-DgraphFormat=text",
        "-DoutputFileName=aggregate-groups");
    byGroupText = MavenFixture.project("by-groupid", "-DgraphFormat=text",
        "-DoutputFileName=collapsed-groups");
    byGroupJson = MavenFixture.project("by-groupid", "-DgraphFormat=json",
        "-DoutputFileName=collapsed-groups");
    aggregateScopesSeparate = MavenFixture.reactor("aggregate", "-DgraphFormat=json",
        "-DmergeScopes=false", "-DreduceEdges=false", "-DoutputFileName=scopes-separate");
    aggregateScopesMerged = MavenFixture.reactor("aggregate", "-DgraphFormat=json",
        "-DmergeScopes=true", "-DreduceEdges=false", "-DoutputFileName=scopes-merged");
    renderedImage = MavenFixture.projectWithFakeGraphviz("rendered-prism");
    externalText = MavenFixture.noProject("for-artifact",
        "-Dartifact=org.junit.jupiter:junit-jupiter-api:5.9.1",
        "-DgraphFormat=text", "-DoutputFileName=external");
    externalJson = MavenFixture.noProject("for-artifact",
        "-Dartifact=org.junit.jupiter:junit-jupiter-api:5.9.1",
        "-DgraphFormat=json", "-DoutputFileName=external");
    externalExcluded = MavenFixture.noProject("for-artifact",
        "-Dartifact=org.junit.jupiter:junit-jupiter-api:5.9.1",
        "-DgraphFormat=json", "-Dexcludes=org.apiguardian:*", "-DoutputFileName=external-filtered");
    invalidExternal = MavenFixture.noProject("for-artifact",
        "-Dartifact=dev.spec2repo.missing:never-present:93.71.4", "-DgraphFormat=text");
    exampleFirst = MavenFixture.builtInExample("-DgraphFormat=json", "-DoutputFileName=example-first");
    exampleSecond = MavenFixture.builtInExample("-DgraphFormat=json", "-DoutputFileName=example-second");
  }

  /** Seam: protocol handoff across graph selection and DOT/JSON serialization. Depends-On: test_dot_projection_contains_declared_dependency_nodes, test_json_projection_contains_declared_artifacts. Verifies: DGM-INV-002, DGM-FMT-003, DGM-FMT-008. */
  @Test void test_dot_and_json_share_selected_project_membership() throws Exception {
    String dotValue = dot.text("target/base.dot");
    JsonNode artifacts = json.json("target/base.json").path("artifacts");
    for (JsonNode artifact : artifacts) {
      assertTrue(dotValue.contains(artifact.path("artifactId").asText()));
    }
  }

  /** Seam: protocol handoff across graph selection and text serialization. Depends-On: test_text_projection_is_rooted_at_fixture_project, test_json_projection_has_named_graph. Verifies: DGM-INV-002, DGM-STATE-001. */
  @Test void test_text_and_json_agree_on_fixture_project_root() throws Exception {
    assertTrue(text.text("target/base.txt").startsWith("amber-lattice"));
    assertTrue(json.text("target/base.json").contains("amber-lattice"));
  }

  /** Seam: protocol handoff across graph selection and GML serialization. Depends-On: test_gml_projection_contains_numeric_nodes_and_edges, test_json_projection_contains_declared_artifacts. Verifies: DGM-INV-002, DGM-FMT-004. */
  @Test void test_gml_and_json_agree_on_artifact_count() throws Exception {
    int gmlNodes = occurrences(gml.text("target/base.gml"), "node [");
    assertEquals(json.json("target/base.json").path("artifacts").size(), gmlNodes);
  }

  /** Seam: protocol handoff across graph selection and PlantUML serialization. Depends-On: test_plantuml_projection_contains_components_and_arrows, test_json_projection_contains_declared_artifacts. Verifies: DGM-INV-002, DGM-FMT-005. */
  @Test void test_plantuml_and_json_agree_on_artifact_membership() throws Exception {
    String plantUml = puml.text("target/base.puml");
    for (JsonNode artifact : json.json("target/base.json").path("artifacts")) {
      assertTrue(plantUml.contains(artifact.path("artifactId").asText()));
    }
  }

  /** JSON relationship fields reference string artifact records. Depends-On: test_json_dependency_has_both_endpoint_schemes, test_json_artifact_has_stable_string_id. Verifies: DGM-FMT-008, DGM-FMT-009, DGM-FMT-010. */
  @Test void test_every_json_edge_references_declared_artifacts() throws Exception {
    JsonNode root = json.json("target/base.json");
    String artifacts = root.path("artifacts").toString();
    for (JsonNode edge : root.path("dependencies")) {
      assertTrue(artifacts.contains(edge.path("from").asText()));
      assertTrue(artifacts.contains(edge.path("to").asText()));
    }
  }

  /** CVI-3: config interaction between excludes and text/JSON projections. Depends-On: test_exclude_pattern_removes_matching_artifact, test_json_projection_contains_declared_dependencies. Verifies: DGM-INV-003, DGM-FILT-009. */
  @Test void test_exclude_filter_removes_artifact_from_text_and_json() throws Exception {
    assertFalse(excludedText.text("target/excluded.txt").contains("jackson-databind"));
    assertFalse(excludedJson.text("target/excluded.json").contains("jackson-databind"));
  }

  /** CVI-3: state consistency of retained neighbors after exclusion. Depends-On: test_exclude_pattern_removes_matching_artifact, test_json_projection_contains_declared_artifacts. Verifies: DGM-INV-003. */
  @Test void test_exclude_filter_preserves_unmatched_artifact_in_both_formats() throws Exception {
    assertTrue(excludedText.text("target/excluded.txt").contains("junit-jupiter-api"));
    assertTrue(excludedJson.text("target/excluded.json").contains("junit-jupiter-api"));
  }

  /** CVI-2: config interaction between includes and DOT/JSON projections. Depends-On: test_include_pattern_limits_declared_project_membership, test_dot_projection_contains_declared_dependency_nodes. Verifies: DGM-INV-002, DGM-FILT-008. */
  @Test void test_include_filter_keeps_matching_artifacts_across_dot_and_json() throws Exception {
    assertTrue(includedDot.text("target/included.dot").contains("junit-jupiter-api"));
    assertTrue(includedJson.text("target/included.json").contains("junit-jupiter-api"));
  }

  /** CVI-3: config interaction between includes and DOT/JSON projections. Depends-On: test_include_pattern_limits_declared_project_membership, test_json_projection_has_named_graph. Verifies: DGM-INV-003, DGM-FILT-008. */
  @Test void test_include_filter_removes_nonmatching_group_across_dot_and_json() throws Exception {
    assertFalse(includedDot.text("target/included.dot").contains("jackson-databind"));
    assertFalse(includedJson.text("target/included.json").contains("jackson-databind"));
  }

  /** CVI-7: lifecycle crossing from path derivation to file persistence. Depends-On: test_missing_custom_output_directory_is_created, test_custom_output_name_gets_format_extension. Verifies: DGM-INV-007, DGM-STATE-002. */
  @Test void test_changing_output_path_preserves_serialized_text_content() throws Exception {
    assertEquals(firstPath.text("first/location/one.txt"), secondPath.text("second/location/two.txt"));
  }

  /** CVI-7: lifecycle crossing across two independently created output directories. Depends-On: test_missing_custom_output_directory_is_created, test_existing_matching_extension_is_not_duplicated. Verifies: DGM-INV-007, DGM-EXEC-009. */
  @Test void test_each_custom_output_path_is_materialized_without_default_file() {
    assertTrue(firstPath.exists("first/location/one.txt"));
    assertTrue(secondPath.exists("second/location/two.txt"));
    assertFalse(firstPath.exists("target/dependency-graph.txt"));
  }

  /** CVI-8: config interaction isolates DOT-only controls from JSON state. Depends-On: test_json_projection_has_named_graph, test_missing_style_fails_while_valid_reference_artifact_exists. Verifies: DGM-INV-008, DGM-STYLE-010. */
  @Test void test_non_dot_projection_ignores_missing_style_and_image_controls() throws Exception {
    assertEquals(0, nonDotMissingStyle.exitCode);
    assertEquals(nonDotStyleBase.text("target/no-style.json"),
        nonDotMissingStyle.text("target/ignored-style.json"));
  }

  /** CVI-8: state consistency keeps JSON membership unchanged by DOT controls. Depends-On: test_json_projection_contains_declared_artifacts, test_missing_style_fails_while_valid_reference_artifact_exists. Verifies: DGM-INV-008, DGM-STATE-003. */
  @Test void test_dot_only_controls_do_not_change_json_artifact_count() throws Exception {
    assertEquals(nonDotStyleBase.json("target/no-style.json").path("artifacts").size(),
        nonDotMissingStyle.json("target/ignored-style.json").path("artifacts").size());
  }

  /** CVI-8: config interaction applies a valid filesystem style to DOT while preserving selected nodes. Depends-On: test_filesystem_custom_style_overrides_dot_attributes, test_dot_projection_contains_declared_dependency_nodes. Verifies: DGM-INV-008, DGM-STYLE-004, DGM-STYLE-006. */
  @Test void test_valid_style_changes_dot_attributes_without_losing_fixture_membership() throws Exception {
    String value = styledDot.text("target/styled-integration.dot");
    assertTrue(value.contains("#123456"));
    assertTrue(value.contains("junit-jupiter-api") && value.contains("jackson-databind"));
  }

  /** CVI-8: state consistency keeps non-DOT graph membership independent of a valid DOT style. Depends-On: test_filesystem_custom_style_overrides_dot_attributes, test_json_projection_contains_declared_artifacts. Verifies: DGM-INV-008, DGM-STYLE-010, DGM-STATE-003. */
  @Test void test_valid_dot_style_does_not_change_json_membership() throws Exception {
    JsonNode baseline = nonDotStyleBase.json("target/no-style.json");
    JsonNode styled = styledJson.json("target/no-style.json");
    assertEquals(baseline.path("artifacts"), styled.path("artifacts"));
    assertEquals(baseline.path("dependencies"), styled.path("dependencies"));
  }

  /** CVI-3: config interaction between target filtering and text/JSON projections. Depends-On: test_include_pattern_limits_declared_project_membership, test_json_projection_contains_declared_dependencies. Verifies: DGM-INV-003, DGM-FILT-011. */
  @Test void test_target_filter_keeps_target_path_across_text_and_json() throws Exception {
    assertTrue(targetText.text("target/targeted.txt").contains("apiguardian-api"));
    assertTrue(targetJson.text("target/targeted.json").contains("apiguardian-api"));
  }

  /** CVI-3: state consistency removes branches not leading to target. Depends-On: test_include_pattern_limits_declared_project_membership, test_json_projection_has_named_graph. Verifies: DGM-INV-003, DGM-FILT-011. */
  @Test void test_target_filter_removes_unrelated_branch_across_formats() throws Exception {
    assertFalse(targetText.text("target/targeted.txt").contains("jackson-databind"));
    assertFalse(targetJson.text("target/targeted.json").contains("jackson-databind"));
  }

  /** Seam: protocol handoff from reactor project graph to DOT serialization. Depends-On: test_default_graph_goal_completes_with_output, test_dot_projection_contains_declared_dependency_nodes. Verifies: DGM-GOAL-012, DGM-FMT-003. */
  @Test void test_reactor_dot_view_contains_module_relationships() throws Exception {
    String value = reactorDot.text("target/reactor.dot");
    assertTrue(value.contains("cobalt-core") && value.contains("mint-service") && value.contains("violet-app"));
  }

  /** Seam: protocol handoff from reactor project graph to JSON serialization. Depends-On: test_json_projection_has_named_graph, test_json_dependency_has_both_endpoint_schemes. Verifies: DGM-GOAL-012, DGM-STATE-001. */
  @Test void test_reactor_json_view_contains_project_edges() throws Exception {
    JsonNode value = reactorJson.json("target/reactor.json");
    assertTrue(value.path("artifacts").size() >= 3);
    assertTrue(value.path("dependencies").size() >= 2);
  }

  /** Seam: config interaction between reactor selection and coordinate display. Depends-On: test_group_id_display_flag_exposes_group_coordinates, test_version_display_flag_exposes_versions. Verifies: DGM-GOAL-013, DGM-ATTR-001. */
  @Test void test_reactor_coordinate_flags_apply_to_selected_project_nodes() throws Exception {
    String value = reactorCoordinates.text("target/reactor-coordinates.txt");
    assertTrue(value.contains("dev.spec2repo.cobalt:cobalt-core:7.3.1"));
    assertTrue(value.contains("dev.spec2repo.violet:violet-app:7.3.1"));
  }

  /** CVI-6: config interaction between edge reduction and aggregate graph reachability. No atomic control exists for aggregate edge reduction. Verifies: DGM-INV-006, DGM-GOAL-010, DGM-GOAL-011. */
  @Test void test_disabling_edge_reduction_retains_more_aggregate_edges() throws Exception {
    int reduced = aggregateReduced.json("target/aggregate-reduced.json").path("dependencies").size();
    int expanded = aggregateExpanded.json("target/aggregate-expanded.json").path("dependencies").size();
    assertTrue(expanded > reduced);
  }

  /** CVI-6: state consistency keeps aggregate nodes while reducing redundant edges. No atomic control exists for aggregate edge reduction. Verifies: DGM-INV-006, DGM-GOAL-004. */
  @Test void test_edge_reduction_preserves_aggregate_node_membership() throws Exception {
    assertEquals(artifactIds(aggregateExpanded.json("target/aggregate-expanded.json")),
        artifactIds(aggregateReduced.json("target/aggregate-reduced.json")));
  }

  /** Seam: config interaction between parent inclusion and aggregate view. No atomic control exists for aggregate parent inclusion. Verifies: DGM-GOAL-005, DGM-GOAL-006. */
  @Test void test_parent_inclusion_changes_aggregate_parent_membership() throws Exception {
    assertTrue(aggregateParents.text("target/aggregate-parents.txt").contains("prism-parent"));
    assertFalse(aggregateNoParents.text("target/aggregate-no-parents.txt").contains("prism-parent"));
  }

  /** Seam: protocol handoff from aggregate selection to group-ID collapse. Depends-On: test_group_id_display_flag_exposes_group_coordinates, test_text_projection_uses_tree_relationship_markers. Verifies: DGM-GOAL-007, DGM-GOAL-008. */
  @Test void test_group_aggregate_projects_cross_group_relationships() throws Exception {
    String value = aggregateByGroup.text("target/aggregate-groups.txt");
    assertTrue(value.contains("dev.spec2repo.cobalt") && value.contains("dev.spec2repo.mint"));
  }

  /** Seam: protocol handoff from dependency selection to group-ID collapse and text serialization. Depends-On: test_text_projection_is_rooted_at_fixture_project, test_group_id_display_flag_exposes_group_coordinates. Verifies: DGM-GOAL-002, DGM-FMT-007. */
  @Test void test_by_groupid_text_collapses_declared_artifacts_to_groups() throws Exception {
    String value = byGroupText.text("target/collapsed-groups.txt");
    assertTrue(value.contains("dev.spec2repo.aurora") && value.contains("org.junit.jupiter"));
    assertFalse(value.contains("amber-lattice") || value.contains("junit-jupiter-api"));
  }

  /** CVI-2: protocol handoff keeps collapsed group membership across text and JSON projections. Depends-On: test_group_id_display_flag_exposes_group_coordinates, test_json_projection_contains_declared_artifacts. Verifies: DGM-GOAL-002, DGM-INV-002, DGM-FMT-008. */
  @Test void test_by_groupid_text_and_json_agree_on_declared_groups() throws Exception {
    String textValue = byGroupText.text("target/collapsed-groups.txt");
    String jsonValue = byGroupJson.text("target/collapsed-groups.json");
    for (String group : new String[] {"dev.spec2repo.aurora", "org.junit.jupiter", "com.fasterxml.jackson.core"}) {
      assertTrue(textValue.contains(group));
      assertTrue(jsonValue.contains(group));
    }
  }

  /** Group-ID collapse omits self-references introduced by the collapse. Depends-On: test_group_id_display_flag_exposes_group_coordinates, test_json_dependency_has_both_endpoint_schemes. Verifies: DGM-GOAL-002, DGM-FMT-010. */
  @Test void test_by_groupid_json_omits_collapsed_self_edges() throws Exception {
    JsonNode dependencies = byGroupJson.json("target/collapsed-groups.json").path("dependencies");
    assertTrue(dependencies.size() > 0);
    for (JsonNode edge : dependencies) {
      assertNotEquals(edge.path("from").asText(), edge.path("to").asText());
    }
  }

  /** CVI-5: config interaction between scope identity and aggregate membership. No atomic control exists for aggregate scope merging. Verifies: DGM-INV-005, DGM-ATTR-010, DGM-ATTR-011. */
  @Test void test_scope_merging_reduces_duplicate_coordinate_nodes() throws Exception {
    int separate = aggregateScopesSeparate.json("target/scopes-separate.json").path("artifacts").size();
    int merged = aggregateScopesMerged.json("target/scopes-merged.json").path("artifacts").size();
    assertTrue(merged < separate);
  }

  /** CVI-5: state consistency exposes combined scopes on the merged node. No atomic control exists for aggregate scope merging. Verifies: DGM-INV-005, DGM-ATTR-010, DGM-FMT-009. */
  @Test void test_scope_merging_exposes_both_effective_scopes() throws Exception {
    JsonNode artifacts = aggregateScopesMerged.json("target/scopes-merged.json").path("artifacts");
    boolean foundMergedArtifact = false;
    for (JsonNode artifact : artifacts) {
      if ("cobalt-core".equals(artifact.path("artifactId").asText())) {
        Set<String> scopes = new HashSet<>();
        artifact.path("scopes").forEach(scope -> scopes.add(scope.asText()));
        if (scopes.contains("compile") && scopes.contains("runtime")) {
          foundMergedArtifact = true;
        }
      }
    }
    assertTrue(foundMergedArtifact);
  }

  /** CVI-9: lifecycle crossing retains DOT source and creates the requested image. Depends-On: test_default_format_is_directed_dot, test_missing_graphviz_fails_while_retaining_valid_reference_control. Verifies: DGM-INV-009, DGM-EXEC-011, DGM-EXEC-012. */
  @Test void test_successful_image_rendering_retains_dot_and_image_outputs() throws Exception {
    assertEquals(0, renderedImage.exitCode);
    assertTrue(renderedImage.exists("target/rendered-prism.dot"));
    assertTrue(renderedImage.exists("target/rendered-prism.png"));
  }

  /** CVI-9: protocol handoff gives Graphviz the same graph execution saved as DOT. Depends-On: test_dot_projection_contains_declared_dependency_nodes, test_missing_graphviz_fails_while_retaining_valid_reference_control. Verifies: DGM-INV-009, DGM-EXEC-011, DGM-EXEC-013. */
  @Test void test_rendered_image_execution_preserves_selected_dot_graph() throws Exception {
    assertTrue(renderedImage.text("target/rendered-prism.dot").contains("amber-lattice"));
    assertTrue(java.nio.file.Files.size(renderedImage.file("target/rendered-prism.png")) > 5);
    java.nio.file.Path recorded = java.nio.file.Paths.get(
        renderedImage.text("graphviz-source.txt").trim()).toRealPath();
    assertEquals(renderedImage.file("target/rendered-prism.dot").toRealPath(), recorded);
  }

  /** CVI-10: protocol handoff from external artifact model to text and JSON projections. Depends-On: test_valid_external_artifact_goal_runs_without_project, test_json_projection_has_named_graph. Verifies: DGM-INV-010, DGM-GOAL-014. */
  @Test void test_external_artifact_root_is_consistent_across_text_and_json() throws Exception {
    assertTrue(externalText.text("external.txt").startsWith("junit-jupiter-api"));
    assertTrue(externalJson.text("external.json").contains("junit-jupiter-api"));
  }

  /** CVI-10: config interaction applies dependency filters after external model creation. Depends-On: test_valid_external_artifact_goal_runs_without_project, test_exclude_pattern_removes_matching_artifact. Verifies: DGM-INV-010, DGM-FILT-009. */
  @Test void test_external_artifact_filter_removes_matching_dependencies() throws Exception {
    assertTrue(externalJson.text("external.json").contains("apiguardian-api"));
    assertFalse(externalExcluded.text("external-filtered.json").contains("apiguardian-api"));
  }

  /** CVI-10: lifecycle crossing writes each external projection in the no-project directory. Depends-On: test_valid_external_artifact_goal_runs_without_project, test_existing_matching_extension_is_not_duplicated. Verifies: DGM-INV-010, DGM-EXEC-005. */
  @Test void test_external_artifact_formats_write_beside_no_project_invocation() {
    assertTrue(externalText.exists("external.txt"));
    assertTrue(externalJson.exists("external.json"));
    assertFalse(externalText.exists("target/external.txt"));
  }

  /** Seam: error propagation from external resolution through Maven execution. Depends-On: test_valid_external_artifact_goal_runs_without_project, test_short_artifact_coordinate_fails_with_positive_control. Verifies: DGM-ERR-003, DGM-ART-009. */
  @Test void test_unresolvable_external_artifact_fails_but_valid_external_flow_succeeds() {
    assertEquals(0, externalText.exitCode);
    assertNotEquals(0, invalidExternal.exitCode);
  }

  /** CVI-1: protocol handoff applies the same output-format contract to graph and reactor views. Depends-On: test_format_selection_is_case_insensitive, test_default_graph_goal_completes_with_output. Verifies: DGM-INV-001, DGM-FMT-001. */
  @Test void test_graph_and_reactor_views_honor_json_projection_contract() throws Exception {
    JsonNode projectGraph = json.json("target/base.json");
    JsonNode reactorGraph = reactorJson.json("target/reactor.json");
    assertTrue(projectGraph.has("graphName") && projectGraph.has("artifacts") && projectGraph.has("dependencies"));
    assertTrue(reactorGraph.has("graphName") && reactorGraph.has("artifacts") && reactorGraph.has("dependencies"));
  }

  /** CVI-1: lifecycle crossing applies output naming to graph and reactor views. Depends-On: test_custom_output_name_gets_format_extension, test_default_graph_goal_writes_to_build_directory. Verifies: DGM-INV-001, DGM-EXEC-008. */
  @Test void test_graph_and_reactor_views_apply_requested_file_names() {
    assertTrue(json.exists("target/base.json"));
    assertTrue(reactorJson.exists("target/reactor.json"));
  }

  /** Seam: state consistency across repeated executions of the built-in example view. Depends-On: test_json_projection_has_named_graph, test_existing_matching_extension_is_not_duplicated. Verifies: DGM-GOAL-003, DGM-STATE-001. */
  @Test void test_built_in_example_is_deterministic_across_independent_runs() throws Exception {
    assertEquals(exampleFirst.text("target/example-first.json"),
        exampleSecond.text("target/example-second.json"));
  }

  /** Seam: config interaction applies common format and output controls to the example view. Depends-On: test_format_selection_is_case_insensitive, test_custom_output_name_gets_format_extension. Verifies: DGM-GOAL-003, DGM-INV-001. */
  @Test void test_built_in_example_honors_json_format_and_output_names() {
    assertEquals(0, exampleFirst.exitCode);
    assertTrue(exampleFirst.exists("target/example-first.json"));
    assertTrue(exampleSecond.exists("target/example-second.json"));
  }

  private static int occurrences(String text, String needle) {
    int count = 0;
    int offset = 0;
    while ((offset = text.indexOf(needle, offset)) >= 0) {
      count++;
      offset += needle.length();
    }
    return count;
  }

  private static Set<String> artifactIds(JsonNode root) {
    Set<String> ids = new HashSet<>();
    for (JsonNode artifact : root.path("artifacts")) {
      ids.add(artifact.path("id").asText());
    }
    return ids;
  }

}
