package atomic;

import com.fasterxml.jackson.databind.JsonNode;
import oraclesupport.MavenFixture;
import oraclesupport.MavenFixture.RunResult;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Black-box atomic checks for documented Maven goal behavior. */
public class ExampleGoalAtomicTest {
  private static RunResult defaultDot;
  private static RunResult json;
  private static RunResult jsonMinimal;
  private static RunResult text;
  private static RunResult gml;
  private static RunResult puml;
  private static RunResult mixedCaseJson;
  private static RunResult customName;
  private static RunResult namedWithExtension;
  private static RunResult artifactFileName;
  private static RunResult customDirectory;
  private static RunResult skipped;
  private static RunResult includes;
  private static RunResult excludes;
  private static RunResult unknownScope;
  private static RunResult classpathRuntime;
  private static RunResult showGroupIds;
  private static RunResult showVersions;
  private static RunResult showTypes;
  private static RunResult hideOptional;
  private static RunResult duplicates;
  private static RunResult resolutionBaseline;
  private static RunResult conflicts;
  private static RunResult conflictsNoVersions;
  private static RunResult invalidFormat;
  private static RunResult missingStyle;
  private static RunResult invalidStyle;
  private static RunResult invalidGraphviz;
  private static RunResult outputWriteFailure;
  private static RunResult shortArtifact;
  private static RunResult mixedArtifact;
  private static RunResult incompleteArtifact;
  private static RunResult validArtifact;
  private static RunResult styledDot;
  private static RunResult printedStyle;

  @BeforeAll
  static void executeReferenceScenarios() throws Exception {
    defaultDot = MavenFixture.project("graph");
    json = MavenFixture.project("graph", "-DgraphFormat=json", "-DoutputFileName=quartz-json");
    jsonMinimal = MavenFixture.project("graph", "-DgraphFormat=json",
        "-DshowAllAttributesForJson=false", "-DoutputFileName=quartz-minimal");
    text = MavenFixture.project("graph", "-DgraphFormat=text", "-DoutputFileName=cedar-tree");
    gml = MavenFixture.project("graph", "-DgraphFormat=gml", "-DoutputFileName=indigo-map");
    puml = MavenFixture.project("graph", "-DgraphFormat=puml", "-DoutputFileName=violet-map");
    mixedCaseJson = MavenFixture.project("graph", "-DgraphFormat=JsOn", "-DoutputFileName=mixed-case");
    customName = MavenFixture.project("graph", "-DgraphFormat=dot", "-DoutputFileName=aurora-map");
    namedWithExtension = MavenFixture.project("graph", "-DgraphFormat=json", "-DoutputFileName=ready.json");
    artifactFileName = MavenFixture.project("graph", "-DgraphFormat=text",
        "-DoutputFileName=ignored-name", "-DuseArtifactIdInFileName=true");
    customDirectory = MavenFixture.project("graph", "-DgraphFormat=gml",
        "-DoutputDirectory=@ROOT@/nested/graph-output", "-DoutputFileName=deep-map");
    skipped = MavenFixture.project("graph", "-Ddepgraph.skip=true", "-DoutputFileName=must-not-exist");
    includes = MavenFixture.project("graph", "-DgraphFormat=text",
        "-Dincludes=dev.spec2repo.aurora:amber-lattice,org.junit.jupiter:*", "-DoutputFileName=included");
    excludes = MavenFixture.project("graph", "-DgraphFormat=text",
        "-Dexcludes=com.fasterxml.jackson.core:jackson-databind", "-DoutputFileName=excluded");
    unknownScope = MavenFixture.project("graph", "-DgraphFormat=text",
        "-Dscopes=compile,ultraviolet", "-DoutputFileName=known-plus-unknown");
    classpathRuntime = MavenFixture.project("graph", "-DgraphFormat=text",
        "-DclasspathScope=runtime", "-DoutputFileName=classpath-runtime");
    showGroupIds = MavenFixture.project("graph", "-DgraphFormat=text",
        "-DshowGroupIds=true", "-DoutputFileName=with-groups");
    showVersions = MavenFixture.project("graph", "-DgraphFormat=text",
        "-DshowVersions=true", "-DoutputFileName=with-versions");
    showTypes = MavenFixture.project("graph", "-DgraphFormat=text",
        "-DshowTypes=true", "-DoutputFileName=with-types");
    hideOptional = MavenFixture.project("graph", "-DgraphFormat=json",
        "-DshowAllAttributesForJson=false", "-DshowOptional=false", "-DoutputFileName=no-optional-marker");
    resolutionBaseline = MavenFixture.project("graph", "-DgraphFormat=json",
        "-DshowAllAttributesForJson=false", "-DoutputFileName=resolution-baseline");
    duplicates = MavenFixture.project("graph", "-DgraphFormat=json",
        "-DshowAllAttributesForJson=false", "-DshowDuplicates=true", "-DoutputFileName=duplicates");
    conflictsNoVersions = MavenFixture.project("graph", "-DgraphFormat=json",
        "-DshowAllAttributesForJson=false", "-DshowConflicts=true", "-DshowVersions=false",
        "-DoutputFileName=conflicts-no-versions");
    conflicts = MavenFixture.project("graph", "-DgraphFormat=json",
        "-DshowAllAttributesForJson=false", "-DshowConflicts=true", "-DshowVersions=true",
        "-DoutputFileName=conflicts");
    String customStyle = "{\"graph\":{\"rankdir\":\"LR\"},"
        + "\"default-node\":{\"type\":\"ellipse\",\"color\":\"#123456\"}}";
    styledDot = MavenFixture.dependencyProjectWithFiles("graph",
        MavenFixture.files("custom-style.json", customStyle),
        "-DgraphFormat=dot", "-DcustomStyleConfiguration=@ROOT@/custom-style.json",
        "-DoutputFileName=styled");
    printedStyle = MavenFixture.dependencyProjectWithFiles("graph",
        MavenFixture.files("custom-style.json", customStyle),
        "-DgraphFormat=dot", "-DcustomStyleConfiguration=@ROOT@/custom-style.json",
        "-DprintStyleConfiguration=true", "-DoutputFileName=printed-style");
    invalidFormat = MavenFixture.project("graph", "-DgraphFormat=matrix42");
    missingStyle = MavenFixture.project("graph", "-DcustomStyleConfiguration=@ROOT@/absent-style.json");
    invalidStyle = MavenFixture.projectWithFiles("example",
        MavenFixture.files("broken-style.json", "{not-json"),
        "-DcustomStyleConfiguration=@ROOT@/broken-style.json");
    invalidGraphviz = MavenFixture.project("graph", "-DcreateImage=true",
        "-DdotExecutable=@ROOT@/missing-dot-binary");
    outputWriteFailure = MavenFixture.projectWithFiles("example",
        MavenFixture.files("occupied", "regular file blocks directory creation"),
        "-DoutputDirectory=@ROOT@/occupied", "-DoutputFileName=blocked-map");
    shortArtifact = MavenFixture.noProject("for-artifact", "-Dartifact=dev.spec2repo:short");
    mixedArtifact = MavenFixture.noProject("for-artifact",
        "-Dartifact=org.junit.jupiter:junit-jupiter-api:5.9.1",
        "-DgroupId=org.junit.jupiter", "-DartifactId=junit-jupiter-api", "-Dversion=5.9.1");
    incompleteArtifact = MavenFixture.noProject("for-artifact", "-DgroupId=com.github.ferstl");
    validArtifact = MavenFixture.noProject("for-artifact",
        "-Dartifact=org.junit.jupiter:junit-jupiter-api:5.9.1",
        "-DgraphFormat=text", "-DoutputFileName=external-root");
  }

  /** Verifies: DGM-EXEC-003, DGM-EXEC-004. */
  @Test void test_default_graph_goal_completes_with_output() {
    assertEquals(0, defaultDot.exitCode);
    assertTrue(defaultDot.exists("target/dependency-graph.dot"));
  }

  /** Verifies: DGM-EXEC-004, DGM-EXEC-006. */
  @Test void test_default_graph_goal_writes_to_build_directory() {
    assertTrue(defaultDot.exists("target/dependency-graph.dot"));
  }

  /** Verifies: DGM-FMT-001, DGM-FMT-003. */
  @Test void test_default_format_is_directed_dot() throws Exception {
    assertTrue(defaultDot.text("target/dependency-graph.dot").contains("digraph"));
  }

  /** Verifies: DGM-FMT-003. */
  @Test void test_dot_projection_contains_declared_dependency_nodes() throws Exception {
    String dot = defaultDot.text("target/dependency-graph.dot");
    assertTrue(dot.contains("junit-jupiter-api") && dot.contains("jackson-databind"));
  }

  /** Verifies: DGM-FMT-008. */
  @Test void test_json_projection_has_named_graph() throws Exception {
    assertEquals(json.json("target/quartz-json.json").path("graphName").asText(),
        jsonMinimal.json("target/quartz-minimal.json").path("graphName").asText());
  }

  /** Verifies: DGM-FMT-008. */
  @Test void test_json_projection_contains_declared_artifacts() throws Exception {
    String value = json.json("target/quartz-json.json").path("artifacts").toString();
    assertTrue(value.contains("junit-jupiter-api") && value.contains("jackson-databind"));
  }

  /** Verifies: DGM-FMT-008. */
  @Test void test_json_projection_contains_declared_dependencies() throws Exception {
    String value = json.json("target/quartz-json.json").path("dependencies").toString();
    assertTrue(value.contains("junit-jupiter-api") && value.contains("jackson-databind"));
  }

  /** Verifies: DGM-FMT-009. */
  @Test void test_json_artifact_has_stable_string_id() throws Exception {
    String artifacts = json.json("target/quartz-json.json").path("artifacts").toString();
    assertTrue(artifacts.contains("dev.spec2repo.aurora:amber-lattice"));
  }

  /** Verifies: DGM-FMT-009. */
  @Test void test_json_artifact_has_unique_numeric_ids() throws Exception {
    java.util.Set<Integer> ids = new java.util.HashSet<>();
    JsonNode artifacts = json.json("target/quartz-json.json").path("artifacts");
    for (JsonNode artifact : artifacts) {
      ids.add(artifact.path("numericId").asInt());
    }
    assertEquals(artifacts.size(), ids.size());
  }

  /** Verifies: DGM-FMT-010. */
  @Test void test_json_dependency_has_both_endpoint_schemes() throws Exception {
    JsonNode edge = json.json("target/quartz-json.json").path("dependencies").get(0);
    assertTrue(edge.has("from") && edge.has("to") && edge.has("numericFrom") && edge.has("numericTo"));
  }

  /** Verifies: DGM-FMT-013, DGM-ATTR-001. */
  @Test void test_json_minimal_mode_omits_disabled_group_field() throws Exception {
    JsonNode artifact = jsonMinimal.json("target/quartz-minimal.json").path("artifacts").get(0);
    assertFalse(artifact.has("groupId"));
  }

  /** Verifies: DGM-FMT-006, DGM-FMT-016, DGM-FMT-017. */
  @Test void test_text_projection_is_rooted_at_fixture_project() throws Exception {
    assertEquals("amber-lattice:compile",
        text.text("target/cedar-tree.txt").lines().findFirst().orElseThrow());
  }

  /** Verifies: DGM-FMT-006. */
  @Test void test_text_projection_uses_tree_relationship_markers() throws Exception {
    String value = text.text("target/cedar-tree.txt");
    assertTrue(value.contains("amber-lattice"));
    assertTrue(value.contains("junit-jupiter-api") && value.contains("jackson-databind"));
  }

  /** Verifies: DGM-FMT-007. */
  @Test void test_text_projection_is_reported_through_maven_output() throws Exception {
    String rootLine = text.text("target/cedar-tree.txt").lines().findFirst().orElseThrow();
    assertTrue(text.output.contains(rootLine));
  }

  /** Verifies: DGM-FMT-010, DGM-STATE-004. */
  @Test void test_json_projection_labels_dependency_resolution() throws Exception {
    JsonNode dependencies = json.json("target/quartz-json.json").path("dependencies");
    assertTrue(dependencies.size() > 0);
    for (JsonNode dependency : dependencies) {
      assertTrue(dependency.has("resolution") && !dependency.path("resolution").asText().isEmpty());
    }
  }

  /** Verifies: DGM-FMT-004. */
  @Test void test_gml_projection_is_directed() throws Exception {
    String value = gml.text("target/indigo-map.gml");
    assertTrue(value.contains("graph [") && value.contains("source ") && value.contains("target "));
  }

  /** Verifies: DGM-FMT-004. */
  @Test void test_gml_projection_contains_numeric_nodes_and_edges() throws Exception {
    String value = gml.text("target/indigo-map.gml");
    assertTrue(value.contains("node [") && value.contains("edge ["));
  }

  /** Verifies: DGM-FMT-005. */
  @Test void test_plantuml_projection_has_document_boundaries() throws Exception {
    String value = puml.text("target/violet-map.puml");
    assertTrue(value.contains("@startuml") && value.contains("@enduml"));
  }

  /** Verifies: DGM-FMT-005. */
  @Test void test_plantuml_projection_contains_components_and_arrows() throws Exception {
    String value = puml.text("target/violet-map.puml");
    assertTrue(value.contains("amber-lattice") && value.contains("junit-jupiter-api") && value.contains("->"));
  }

  /** Verifies: DGM-FMT-001. */
  @Test void test_format_selection_is_case_insensitive() {
    assertEquals(0, mixedCaseJson.exitCode);
    assertTrue(mixedCaseJson.exists("target/mixed-case.json"));
  }

  /** Verifies: DGM-EXEC-006, DGM-EXEC-008. */
  @Test void test_custom_output_name_gets_format_extension() {
    assertTrue(customName.exists("target/aurora-map.dot"));
  }

  /** Verifies: DGM-EXEC-008. */
  @Test void test_existing_matching_extension_is_not_duplicated() {
    assertTrue(namedWithExtension.exists("target/ready.json"));
    assertFalse(namedWithExtension.exists("target/ready.json.json"));
  }

  /** Verifies: DGM-EXEC-007. */
  @Test void test_artifact_id_can_replace_output_file_name() {
    assertTrue(artifactFileName.exists("target/amber-lattice.txt"));
    assertFalse(artifactFileName.exists("target/ignored-name.txt"));
  }

  /** Verifies: DGM-EXEC-009. */
  @Test void test_missing_custom_output_directory_is_created() {
    assertTrue(customDirectory.exists("nested/graph-output/deep-map.gml"));
  }

  /** Verifies: DGM-EXEC-002. */
  @Test void test_skip_completes_without_writing_output() {
    assertTrue(defaultDot.exists("target/dependency-graph.dot"));
    assertEquals(0, skipped.exitCode);
    assertFalse(skipped.exists("target/must-not-exist.dot"));
  }

  /** Verifies: DGM-FILT-007, DGM-FILT-008. */
  @Test void test_include_pattern_limits_declared_project_membership() throws Exception {
    String value = includes.text("target/included.txt");
    assertTrue(value.contains("junit-jupiter-api"));
    assertFalse(value.contains("jackson-databind"));
  }

  /** Verifies: DGM-FILT-007, DGM-FILT-009. */
  @Test void test_exclude_pattern_removes_matching_artifact() throws Exception {
    String value = excludes.text("target/excluded.txt");
    assertTrue(value.contains("junit-jupiter-api"));
    assertFalse(value.contains("jackson-databind"));
  }

  /** Verifies: DGM-FILT-003, DGM-ERR-007. */
  @Test void test_unknown_scope_is_ignored_beside_known_scope() throws Exception {
    assertEquals(0, unknownScope.exitCode);
    String value = unknownScope.text("target/known-plus-unknown.txt");
    assertTrue(value.contains("junit-jupiter-api"));
    assertTrue(value.contains("junit-platform-commons"));
    assertFalse(value.contains("jackson-databind"));
    assertFalse(value.contains("junit-jupiter-engine"));
  }

  /** Verifies: DGM-FILT-004. */
  @Test void test_runtime_classpath_scope_includes_compile_and_runtime() throws Exception {
    String value = classpathRuntime.text("target/classpath-runtime.txt");
    assertTrue(value.contains("junit-jupiter-api:compile") && value.contains("jackson-databind:runtime"));
    assertFalse(value.contains("junit-jupiter-engine:test"));
  }

  /** Verifies: DGM-ATTR-001. */
  @Test void test_group_id_display_flag_exposes_group_coordinates() throws Exception {
    assertTrue(showGroupIds.text("target/with-groups.txt").contains("dev.spec2repo.aurora:amber-lattice"));
  }

  /** Verifies: DGM-ATTR-001, DGM-FMT-016, DGM-FMT-017. */
  @Test void test_version_display_flag_exposes_versions() throws Exception {
    assertTrue(showVersions.text("target/with-versions.txt")
        .contains("junit-jupiter-api:5.9.1:compile"));
  }

  /** Verifies: DGM-ATTR-001, DGM-FMT-016, DGM-FMT-017. */
  @Test void test_type_display_flag_exposes_packaging() throws Exception {
    assertTrue(showTypes.text("target/with-types.txt")
        .contains("junit-jupiter-api:jar:compile"));
  }

  /** Verifies: DGM-ATTR-002, DGM-FMT-013. */
  @Test void test_optional_field_is_absent_when_optional_display_disabled() throws Exception {
    JsonNode artifact = hideOptional.json("target/no-optional-marker.json").path("artifacts").get(0);
    assertFalse(artifact.has("optional"));
  }

  /** Verifies: DGM-ATTR-004. */
  @Test void test_duplicate_display_adds_duplicate_resolution() throws Exception {
    int baseline = resolutionBaseline.json("target/resolution-baseline.json").path("dependencies").size();
    int expanded = duplicates.json("target/duplicates.json").path("dependencies").size();
    assertTrue(expanded > baseline);
  }

  /** Verifies: DGM-ATTR-005, DGM-ATTR-006. */
  @Test void test_conflict_display_exposes_omitted_and_selected_versions() throws Exception {
    int baseline = resolutionBaseline.json("target/resolution-baseline.json").path("dependencies").size();
    JsonNode expanded = conflicts.json("target/conflicts.json").path("dependencies");
    assertTrue(expanded.size() > baseline);
    JsonNode withoutVersions = conflictsNoVersions.json("target/conflicts-no-versions.json").path("dependencies");
    assertNotEquals(withoutVersions.toString(), expanded.toString());
  }

  /** Verifies: DGM-STYLE-004, DGM-STYLE-006, DGM-STYLE-007. */
  @Test void test_filesystem_custom_style_overrides_dot_attributes() throws Exception {
    assertEquals(0, styledDot.exitCode);
    String value = styledDot.text("target/styled.dot");
    assertTrue(value.contains("LR") && value.contains("#123456"));
  }

  /** Verifies: DGM-STYLE-004, DGM-STYLE-007, DGM-STYLE-009. */
  @Test void test_print_style_configuration_reports_effective_override() {
    assertTrue(printedStyle.exists("target/printed-style.dot"));
    assertTrue(printedStyle.output.contains("#123456"));
  }

  /** Verifies: DGM-FMT-002, DGM-ERR-001. */
  @Test void test_invalid_format_fails_while_valid_reference_artifact_exists() {
    assertTrue(defaultDot.exists("target/dependency-graph.dot"));
    assertNotEquals(0, invalidFormat.exitCode);
  }

  /** Verifies: DGM-STYLE-008, DGM-ERR-004. */
  @Test void test_missing_style_fails_while_valid_reference_artifact_exists() {
    assertTrue(defaultDot.exists("target/dependency-graph.dot"));
    assertNotEquals(0, missingStyle.exitCode);
  }

  /** Verifies: DGM-STYLE-008, DGM-ERR-004. */
  @Test void test_invalid_style_fails_while_valid_reference_artifact_exists() {
    assertTrue(defaultDot.exists("target/dependency-graph.dot"));
    assertNotEquals(0, invalidStyle.exitCode);
  }

  /** Verifies: DGM-EXEC-014, DGM-ERR-006. */
  @Test void test_missing_graphviz_fails_while_retaining_valid_reference_control() {
    assertTrue(defaultDot.exists("target/dependency-graph.dot"));
    assertNotEquals(0, invalidGraphviz.exitCode);
  }

  /** Verifies: DGM-EXEC-010, DGM-ERR-005. */
  @Test void test_unwritable_output_target_fails_while_valid_reference_artifact_exists() {
    assertTrue(defaultDot.exists("target/dependency-graph.dot"));
    assertNotEquals(0, outputWriteFailure.exitCode);
  }

  /** Verifies: DGM-ART-007, DGM-ERR-002. */
  @Test void test_short_artifact_coordinate_fails_with_positive_control() {
    assertEquals(0, validArtifact.exitCode);
    assertNotEquals(0, shortArtifact.exitCode);
  }

  /** Verifies: DGM-ART-006, DGM-ERR-002. */
  @Test void test_mixed_artifact_coordinate_forms_fail_with_positive_control() {
    assertTrue(validArtifact.exists("external-root.txt"));
    assertNotEquals(0, mixedArtifact.exitCode);
  }

  /** Verifies: DGM-ART-002, DGM-ART-008, DGM-ERR-002. */
  @Test void test_incomplete_long_coordinate_form_fails_with_positive_control() throws Exception {
    assertTrue(validArtifact.text("external-root.txt").contains("junit-jupiter-api"));
    assertNotEquals(0, incompleteArtifact.exitCode);
  }

  /** Verifies: DGM-ART-001, DGM-GOAL-014, DGM-EXEC-005. */
  @Test void test_valid_external_artifact_goal_runs_without_project() {
    assertEquals(0, validArtifact.exitCode);
    assertTrue(validArtifact.exists("external-root.txt"));
  }
}
